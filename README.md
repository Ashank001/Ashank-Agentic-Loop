# Agentic Loop Demo

An advanced cognitive AI agent loop that processes unstructured meeting notes and extracts actionable items using the ReAct (Reason + Act) and Reflexion frameworks. The agent features persistent memory across sessions to recall information previously learned.

## Features

- **ReAct Framework**: The agent intelligently reasons when to call tools to fetch missing data (e.g., resolving first names to emails via a mock directory or parsing relative dates like "tomorrow").
- **Reflexion**: Built-in self-evaluation step that programmatically audits the action items against strict SMART criteria.
- **Persistent Memory**: Uses [Mem0](https://github.com/mem0ai/mem0) (backed by ChromaDB) to remember user details across multiple sessions.
- **Resilient Harness**: Custom exponential backoff, rate limit handling, infinite loop detection, and JSON normalization ensure the agent remains robust even when the LLM misbehaves or rate limits are hit.
- **Structured Logging**: Execution logs are cleanly outputted to `logs/agent_execution.log` in a structured JSON format for observability.

## Prerequisites

- Python 3.9+
- A [Groq API Key](https://console.groq.com/keys)
- A [Hugging Face Token](https://huggingface.co/settings/tokens) (Optional, but highly recommended to avoid rate limits when downloading embeddings)

## Setup & Installation

1. **Clone the repository and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You may need to run `pip install mem0ai[nlp]` if you see spaCy errors during execution)*

2. **Configure Environment Variables:**
   Copy the example environment file and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   Add your keys to the `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   HF_TOKEN=your_huggingface_token_here
   ```

3. **Configure Settings (Optional):**
   You can adjust the LLM model, temperature, and agent loop constraints in `config.yaml`.

## Usage

Run the main script to start the demo:
```bash
python main.py
```

### The Demo Flow

The script will automatically run through two sessions to demonstrate the agent's capabilities:

- **Session 1**: The agent parses notes like *"Dave needs to fix the API endpoint by tomorrow"*. It will realize "Dave" is ambiguous, use its tools to look up his full email address, parse the relative date, and save Dave's email to its long-term memory.
- **Session 2**: A follow-up note is parsed (*"Dave needs to write the documentation..."*). The agent will seamlessly recall Dave's email from the vector database without needing to query the mock directory tool again.

## Architecture Highlights

- `agent/loop.py`: The core ReAct and Reflexion loop logic.
- `agent/tools.py`: Tool definitions (JSON schema) and execution handlers.
- `agent/memory_manager.py`: Long-term memory storage using Mem0 and Chroma.
- `agent/harness.py`: Resilience wrappers (retries, rate-limit parsing, etc.).
- `agent/prompts.py`: The system prompts driving the agent's behavior.
