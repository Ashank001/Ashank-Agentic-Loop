import os
from agent.loop import run_agent
from agent.memory_manager import AgentMemory

def read_notes(filename: str) -> str:
    """Helper function to read meeting notes from the data directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", filename)
    try:
        with open(data_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Could not find {data_path}")
        return ""

def main():
    agent_memory = AgentMemory()
    
    print("🧹 Clearing previous memories for a clean demo run...\n")
    agent_memory.clear(user_id="demo_user")
    
    # Load the data files
    notes_1 = read_notes("session_1.txt")
    notes_2 = read_notes("session_2.txt")
    
    if not notes_1 or not notes_2:
        print("Missing sample data files. Please create them in the data/ directory.")
        return

    print("=====================================================")
    print("🎬 SESSION 1: First meeting — agent looks up emails.")
    print("=====================================================")
    print(f"Raw Input: {notes_1}")
    run_agent(notes_1, user_id="demo_user")
    
    print("\n\n=====================================================")
    print("🎬 SESSION 2: Follow-up — agent SHOULD remember emails!")
    print("=====================================================")
    print(f"Raw Input: {notes_2}")
    run_agent(notes_2, user_id="demo_user")

if __name__ == "__main__":
    main()