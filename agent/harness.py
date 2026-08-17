import time
import random
import functools
import yaml

# Load runtime parameters from config (satisfies Config requirement)
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

def with_backoff(max_retries=3, base_delay=1):
    """Exponential backoff with jitter for LLM API calls."""
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
                        
                    # Jitter formula: (base_delay * 2^retry) + random milliseconds
                    delay = (base_delay * (2 ** (retries - 1))) + random.uniform(0.1, 1.0)
                    
                    # Fallback Strategy 1: LLM returns unparseable output or times out
                    print(f'{{ "harness_retry": "Exception in {func.__name__}: {error_msg}. Retrying in {delay:.2f}s..." }}')
                    time.sleep(delay)
        return wrapper
    return decorator