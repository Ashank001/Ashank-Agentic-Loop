import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from agent.prompts import PERCEIVE_PROMPT, REASON_PROMPT, REFLECT_PROMPT
from agent.tools import TOOL_HANDLERS
from agent.memory_manager import AgentMemory
from agent.harness import with_backoff, CONFIG
from agent.logger import agent_logger

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
MODEL_NAME = CONFIG['llm']['model_name']
MAX_ITERATIONS = CONFIG['agent']['max_iterations']
TOKEN_WARNING_LIMIT = CONFIG['agent']['token_budget_warning']

agent_memory = AgentMemory()

# Global token counter for guardrails
total_session_tokens = 0

import re as _re

def _extract_json(text: str) -> dict:
    """Extract JSON from LLM output, stripping <think> tags, markdown fences, etc."""
    # Strip thinking tags from reasoning models like Qwen
    text = _re.sub(r'<think>.*?</think>', '', text, flags=_re.DOTALL).strip()
    # Strip markdown code fences if present
    text = _re.sub(r'```json\s*', '', text)
    text = _re.sub(r'```\s*', '', text)
    # Try parsing directly first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: find the first JSON object or array in the text
    match = _re.search(r'(\{.*\}|\[.*\])', text, _re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}")

@with_backoff(max_retries=3, base_delay=2)
def _call_llm(system_prompt: str, user_content: str) -> dict:
    global total_session_tokens
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=CONFIG['llm']['temperature']
    )
    
    # Track Token Budget
    total_session_tokens += response.usage.total_tokens
    if total_session_tokens > TOKEN_WARNING_LIMIT:
        print(f'{{ "guardrail_warning": "Token budget exceeded ({total_session_tokens}/{TOKEN_WARNING_LIMIT})" }}')
    
    raw_content = response.choices[0].message.content
    parsed = _extract_json(raw_content)
    
    # Normalize: some models return a list instead of a dict
    if isinstance(parsed, list):
        parsed = parsed[0] if parsed and isinstance(parsed[0], dict) else {"action_items": parsed}
    
    return parsed

def perceive(input_data: str, previous_feedback: str = None) -> dict:
    agent_logger.start_step("perceive")
    content = f"Meeting Notes:\n{input_data}"
    if previous_feedback:
        content += f"\n\nPrevious Reflection Feedback:\n{previous_feedback}"
    
    result = _call_llm(PERCEIVE_PROMPT, content)
    agent_logger.log_step(0, "perceive", content, result)
    return result

def reason(observation: dict, memory_context: list, iteration: int) -> dict:
    agent_logger.start_step("reason")
    content = f"Current Observation:\n{json.dumps(observation)}\n"
    if memory_context:
        content += f"\nPast Memories:\n{json.dumps(memory_context)}\nUse these memories to resolve missing info."
    
    result = _call_llm(REASON_PROMPT, content)
    agent_logger.log_step(iteration, "reason", content, result)
    return result

def act(plan: dict, tools: dict, iteration: int) -> dict:
    agent_logger.start_step("act")
    if plan.get("action") == "COMPLETE":
        result = {"status": "success", "data": "No tool needed."}
        agent_logger.log_step(iteration, "act", plan, result)
        return result
        
    tool_name = plan.get("tool_name")
    tool_args = plan.get("tool_args", {})
    
    try:
        if tool_name in tools:
            output = tools[tool_name](**tool_args)
            result = {"tool_name": tool_name, "result": output}
        else:
            result = {"error": f"Tool '{tool_name}' not found."}
    except Exception as e:
        # Fallback Strategy 2: Tool call fails -> Return graceful error
        result = {"tool_name": tool_name, "error": f"Tool crash handled: {str(e)}"}
        
    agent_logger.log_step(iteration, "act", plan, result)
    return result

def reflect(result: dict, observation: dict, iteration: int) -> dict:
    agent_logger.start_step("reflect")
    content = f"Action Result:\n{json.dumps(result)}\n\nObservation:\n{json.dumps(observation)}"
    
    output = _call_llm(REFLECT_PROMPT, content)
    agent_logger.log_step(iteration, "reflect", content, output)
    return output

def run_agent(raw_notes: str, user_id: str = "demo_user"):
    global total_session_tokens
    total_session_tokens = 0 # Reset for new session
    
    observation = perceive(raw_notes)
    previous_reflection_hash = None
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        # Fallback Strategy 4: Memory read failure -> continue with warning
        try:
            memory_context = agent_memory.recall(str(observation.get("action_items", [])), user_id=user_id)
        except Exception as e:
            print(f'{{ "harness_warning": "Memory read failed: {str(e)}. Continuing without memory." }}')
            memory_context = []
            
        plan = reason(observation, memory_context, iteration)
        result = act(plan, TOOL_HANDLERS, iteration)
        reflection = reflect(result, observation, iteration)
        
        # Guardrail: Infinite Loop Detection (STUCK)
        current_reflection_hash = hash(str(reflection.get("critique", "")) + str(reflection.get("next_instruction", "")))
        if current_reflection_hash == previous_reflection_hash:
            print('{ "guardrail_trigger": "STUCK_STATE_DETECTED - Identical reflection twice. Breaking loop." }')
            observation["status"] = "STUCK"
            break
        previous_reflection_hash = current_reflection_hash
        
        if reflection.get("is_done"):
            observation["status"] = "COMPLETE"
            for task in observation.get("action_items", []):
                owner = task.get("owner")
                if owner and "@" in owner:
                    try:
                        agent_memory.save(f"The email address for the owner of task '{task.get('description')}' is {owner}", user_id=user_id)
                    except Exception as e:
                        print(f'{{ "harness_warning": "Memory write failed: {str(e)}" }}')
            break
            
        observation = perceive(json.dumps(observation), reflection.get('next_instruction'))
        
    else:
        # Fallback Strategy 3: Max iterations reached
        observation["status"] = "PARTIAL"
        
    print("\n--- FINAL RESULT ---")
    print(json.dumps(observation, indent=2))
    return observation