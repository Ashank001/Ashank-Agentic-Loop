import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from agent.prompts import PERCEIVE_PROMPT, REASON_PROMPT, REFLECT_PROMPT
from agent.tools import TOOL_HANDLERS
from agent.memory_manager import AgentMemory # <-- NEW IMPORT

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
MODEL_NAME = "llama-3.3-70b-versatile"

# Initialize memory manager
agent_memory = AgentMemory() # <-- NEW INITIALIZATION

def _call_llm(system_prompt: str, user_content: str) -> dict:
    # (Same as before)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    return json.loads(response.choices[0].message.content)

def perceive(input_data: str, previous_feedback: str = None) -> dict:
    # (Same as before)
    print("\n[PERCEIVE] Analyzing input...")
    content = f"Meeting Notes:\n{input_data}"
    if previous_feedback:
        content += f"\n\nPrevious Reflection Feedback:\n{previous_feedback}"
    return _call_llm(PERCEIVE_PROMPT, content)

def reason(observation: dict, memory_context: list) -> dict:
    """Call the LLM to decide what to do next, now with memory context."""
    print("[REASON] Deciding next action...")
    content = f"Current Observation:\n{json.dumps(observation, indent=2)}\n"
    
    # <-- INJECT MEMORY INTO PROMPT
    if memory_context:
        content += f"\nRelevant Past Memories:\n{json.dumps(memory_context, indent=2)}\nUse these memories to resolve missing info WITHOUT calling tools if possible."
    
    return _call_llm(REASON_PROMPT, content)

def act(plan: dict, tools: dict) -> dict:
    # (Same as before)
    print(f"[ACT] Executing action based on plan...")
    action = plan.get("action")
    if action == "COMPLETE":
        return {"status": "success", "data": "No tool needed, task complete."}
    tool_name = plan.get("tool_name")
    tool_args = plan.get("tool_args", {})
    if tool_name in tools:
        print(f"        -> Calling {tool_name} with {tool_args}")
        try:
            result = tools[tool_name](**tool_args)
            return {"tool_name": tool_name, "result": result}
        except Exception as e:
            return {"tool_name": tool_name, "error": str(e)}
    else:
        return {"error": f"Tool '{tool_name}' not found."}

def reflect(result: dict, observation: dict) -> dict:
    # (Same as before)
    print("[REFLECT] Evaluating state...")
    content = f"Latest Action Result:\n{json.dumps(result, indent=2)}\n\nCurrent Observation:\n{json.dumps(observation, indent=2)}"
    return _call_llm(REFLECT_PROMPT, content)

def run_agent(raw_notes: str, user_id: str = "project_alpha", max_iterations: int = 5):
    """The Core Agentic Loop with Memory integration."""
    print(f"=== STARTING AGENTIC LOOP (User: {user_id}) ===")
    
    observation = perceive(raw_notes)
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")
        
        # <-- RECALL MEMORY BEFORE REASONING
        # We search memory using the current extracted entities
        memory_context = agent_memory.recall(str(observation.get("action_items", [])), user_id=user_id)
        
        plan = reason(observation, memory_context)
        print(f"        -> Thought: {plan.get('thought')}")
        
        result = act(plan, TOOL_HANDLERS)
        
        reflection = reflect(result, observation)
        print(f"        -> Score: {reflection.get('quality_score')}/100")
        print(f"        -> Critique: {reflection.get('critique')}")
        
        if reflection.get("is_done"):
            print("\n[SUCCESS] Goal achieved!")
            print(json.dumps(observation, indent=2))
            
            # <-- SAVE WHAT WE LEARNED AFTER SUCCESS
            # If we successfully resolved tasks, save the mapping so the agent remembers it next time!
            for task in observation.get("action_items", []):
                owner = task.get("owner")
                if owner and "@" in owner:
                    agent_memory.save(f"The email address for the owner of task '{task.get('description')}' is {owner}", user_id=user_id)
            break
            
        print(f"        -> Next Instruction: {reflection.get('next_instruction')}")
        observation = perceive(json.dumps(observation), reflection.get('next_instruction'))
        
    else:
        print("\n[STOPPED] Max iterations reached without completion.")