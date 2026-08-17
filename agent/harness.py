import time
import re
import random
import functools
import yaml

# Load runtime parameters from config (satisfies Config requirement)
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

def _parse_retry_after(error_msg: str) -> float:
    """Extract the wait time from a Groq 429 error message like 'try again in 3m23.904s'."""
    match = re.search(r'try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s', error_msg, re.IGNORECASE)
    if match:
        minutes = int(match.group(1)) if match.group(1) else 0
        seconds = float(match.group(2))
        return (minutes * 60) + seconds + 1  # Add 1s safety margin
    return None

def with_backoff(max_retries=3, base_delay=1):
    """Exponential backoff with jitter for LLM API calls.
    Handles 429 rate limits specially by parsing the server's suggested wait time."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    error_msg = str(e)
                    
                    if retries == max_retries:
                        print(f'{{ "harness_fatal": "Failed after {max_retries} attempts. Error: {error_msg}" }}')
                        raise e
                    
                    # Check if this is a 429 rate limit with a specific wait time
                    retry_after = _parse_retry_after(error_msg)
                    if retry_after and "rate_limit" in error_msg.lower():
                        delay = retry_after
                        print(f'{{ "harness_rate_limit": "Rate limited. Waiting {delay:.0f}s as instructed by server..." }}')
                    else:
                        # Standard jitter formula: (base_delay * 2^retry) + random milliseconds
                        delay = (base_delay * (2 ** (retries - 1))) + random.uniform(0.1, 1.0)
                        # Fallback Strategy 1: LLM returns unparseable output or times out
                        print(f'{{ "harness_retry": "Exception in {func.__name__}: {error_msg}. Retrying in {delay:.2f}s..." }}')
                    
                    time.sleep(delay)
        return wrapper
    return decorator