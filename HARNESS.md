# Harness Engineering & Resiliency 

A cognitive agent is inherently non-deterministic. Without a production-grade harness, temporary network drops, hallucinated JSON, or edge-case inputs will cause the loop to crash or burn excessive compute. 

Below are the engineering decisions implemented in `agent/harness.py`, `agent/logger.py`, and `agent/loop.py` to defend against these failure modes.

## 1. Retry Logic & Jitter
* **Engineering Decision:** Implemented a custom `@with_backoff` decorator for all LLM API calls. It uses the formula `(base_delay * 2^retry) + random(0.1, 1.0)`.
* **Defends Against:** 
  * HTTP 429 (Rate Limits) and HTTP 5xx (Server Errors) from the LLM provider.
  * The random jitter prevents the "thundering herd" problem, ensuring that if multiple agent threads fail simultaneously, they don't all retry at the exact same millisecond and re-trigger rate limits.

## 2. Fallback Strategies
| Failure Mode | Fallback Decision | Defends Against |
| :--- | :--- | :--- |
| **LLM Exception / Parse Failure** | The `@with_backoff` decorator catches the exception, logs it, and retries the prompt. After `max_retries`, it raises a fatal error. | LLM connection timeouts or the model returning malformed (non-JSON) text that breaks `json.loads`. |
| **Tool Call Fails** | Wrapped tool execution in `try/except`. If a tool crashes, it catches the error and returns a graceful JSON payload: `{"error": "Tool crash handled..."}`. | The entire agent crashing due to a bug in a downstream tool or a hallucinated parameter. It allows the LLM to read the error and try a different approach. |
| **Max Iterations Reached** | Utilizing Python's `for/else` construct on the main loop. If it finishes without `break`, it flags `observation["status"] = "PARTIAL"`. | Runaway agents burning tokens on unsolvable ambiguity. Returns the best-effort draft instead of failing silently. |
| **Memory Read/Write Failure** | Wrapped `agent_memory.recall` and `save` in `try/except` blocks. If they fail, the agent logs a warning and proceeds with empty `memory_context = []`. | I/O locks, file permission issues, or vector DB corruption halting the primary task of extracting action items. |

## 3. Loop Guardrails
* **Infinite Loop Detection (STUCK State):** 
  * *Decision:* The loop calculates a runtime hash of the `reflect` step's output (`critique` + `next_instruction`). If the current hash perfectly matches the previous iteration's hash, the agent is repeating itself. The harness instantly breaks the loop and flags it as `STUCK`.
  * *Defends Against:* Logic locks where the LLM continuously generates the exact same failed plan without adapting, burning tokens endlessly.
* **Token Budget Tracking:** 
  * *Decision:* A global `total_session_tokens` counter increments via the LLM API's `usage.total_tokens` response. If it exceeds the `token_budget_warning` set in `config.yaml`, a structured telemetry warning is emitted.
  * *Defends Against:* Unnoticed compute cost spikes.

## 4. Observability (Structured JSON)
* **Engineering Decision:** Built a custom `AgentLogger` that records `timestamp`, `latency_ms`, `iteration`, and truncated `input/output` summaries. It writes a flat JSON line to both stdout and a physical file (`logs/agent_execution.log`).
* **Defends Against:** Blind debugging. When agents fail at scale, standard text logs are impossible to query. Structured JSON lines allow seamless ingestion into Datadog or Elasticsearch to monitor average reasoning latency and tool error rates.