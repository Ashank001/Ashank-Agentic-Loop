import os
from agent.loop import run_agent

def main():
    # Construct the path to the sample meeting notes
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "sample_meeting.txt")
    
    # Read the mock data
    try:
        with open(data_path, "r") as f:
            raw_notes = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {data_path}")
        print("Please create 'data/sample_meeting.txt' with some sample notes.")
        return

    print("Loaded Meeting Notes:")
    print("-" * 40)
    print(raw_notes.strip())
    print("-" * 40)
    
    # Run the agent loop
    # We set max_iterations to 5 for safety during testing
    run_agent(raw_notes, max_iterations=5)

if __name__ == "__main__":
    main()