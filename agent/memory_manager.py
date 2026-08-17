import os
from mem0 import Memory

class AgentMemory:
    def __init__(self):
        # Configure Mem0 to use local ChromaDB
        db_path = os.path.join(os.getcwd(), "chroma_db")
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "agentic_memory",
                    "path": db_path
                }
            }
        }
        self.memory = Memory.from_config(config)

    def save(self, text: str, user_id: str = "default_user"):
        """Saves a new memory or updates an existing conflicting one."""
        print(f"    [MEMORY SAVE] Storing: {text[:50]}...")
        self.memory.add(text, user_id=user_id)

    def recall(self, query: str, user_id: str = "default_user") -> list:
        """Retrieves relevant memories based on the query."""
        print(f"    [MEMORY RECALL] Searching past context for: {query[:30]}...")
        results = self.memory.search(query, user_id=user_id)
        
        # Extract just the text from the Mem0 result objects
        memories = [r.get('memory', '') for r in results] if results else []
        return memories

    def clear(self, user_id: str = "default_user"):
        """Wipes memory for the user."""
        self.memory.delete_all(user_id=user_id)