import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from agent.prompts import PERCEIVE_PROMPT, REASON_PROMPT, REFLECT_PROMPT
from agent.tools import TOOL_HANDLERS

# Load environment variables
load_dotenv()

# Initialize the Groq client (using OpenAI SDK for compatibility)
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
MODEL_NAME = "llama-3.3-70b-versatile"

def _call_llm(system_prompt: str, user_content: str) -> dict:
    """Helper function to call the LLM and force JSON output."""
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
    """Parse and structure raw input."""
    print("\n[PERCEIVE] Analyzing input...")
    content = f"Meeting Notes:\n{input_data}"
    if previous_feedback:
        content += f"\n\nPrevious Reflection Feedback:\n{previous_feedback}"
        
    return _call_llm(PERCEIVE_PROMPT, content)

def reason(observation: dict, memory: list) -> dict:
    """Call the LLM to decide what to do next."""
    print("[REASON] Deciding next action...")
    content = f"Current Observation:\n{json.dumps(observation, indent=2)}"
    # memory will be integrated in Milestone 2
    
    return _call_llm(REASON_PROMPT, content)

def act(plan: dict, tools: dict) -> dict:
    """Execute the planned action by calling the appropriate tool."""
    print(f"[ACT] Executing action based on plan...")
    
    action = plan.get("action")
    if action == "COMPLETE":
        return {"status": "success", "data": "No tool needed, task complete."}
        
    tool_name = plan.get("tool_name")
    tool_args = plan.get("tool_args", {})
    
    if tool_name in tools:
        print(f"        -> Calling {tool_name} with {tool_args}")
        try:
            # THIS is where the Python function is actually executed!
            result = tools[tool_name](**tool_args)
            return {"tool_name": tool_name, "result": result}
        except Exception as e:
            return {"tool_name": tool_name, "error": str(e)}
    else:
        return {"error": f"Tool '{tool_name}' not found."}

def reflect(result: dict, observation: dict) -> dict:
    """Evaluate whether the goal was met."""
    print("[REFLECT] Evaluating state...")
    content = f"Latest Action Result:\n{json.dumps(result, indent=2)}\n\nCurrent Observation:\n{json.dumps(observation, indent=2)}"
    
    return _call_llm(REFLECT_PROMPT, content)

def run_agent(raw_notes: str, max_iterations: int = 5):
    """The Core Agentic Loop"""
    print("=== STARTING AGENTIC LOOP ===")
    
    # 1. Initial Perception
    observation = perceive(raw_notes)
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- Iteration {iteration} ---")
        
        # 2. Reason
        plan = reason(observation, memory=[])
        print(f"        -> Thought: {plan.get('thought')}")
        
        # 3. Act
        result = act(plan, TOOL_HANDLERS)
        
        # 4. Reflect
        reflection = reflect(result, observation)
        print(f"        -> Score: {reflection.get('quality_score')}/100")
        print(f"        -> Critique: {reflection.get('critique')}")
        
        if reflection.get("is_done"):
            print("\n[SUCCESS] Goal achieved!")
            print(json.dumps(observation, indent=2))
            break
            
        # If not done, feed reflection back into perceive for next loop
        print(f"        -> Next Instruction: {reflection.get('next_instruction')}")
        observation = perceive(json.dumps(observation), reflection.get('next_instruction'))
        
    else:
        print("\n[STOPPED] Max iterations reached without completion.")