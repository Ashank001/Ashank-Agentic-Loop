import os
from mem0 import Memory
from dotenv import load_dotenv

# Ensure environment variables are loaded so Mem0 can see GROQ_API_KEY
load_dotenv()

class AgentMemory:
    def __init__(self):
        db_path = os.path.join(os.getcwd(), "chroma_db")
        
        # Explicitly configure Mem0 to use free providers instead of default OpenAI
        config = {
            "llm": {
                "provider": "groq",
                "config": {
                    "model": "llama-3.3-70b-versatile"
                    # It will automatically use the GROQ_API_KEY from your .env file
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            },
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
        print(f"    [MEMORY SAVE] Mem0 is structuring and storing fact: {text[:50]}...")
        self.memory.add(text, user_id=user_id)

    def recall(self, query: str, user_id: str = "default_user") -> list:
        """Retrieves relevant memories based on the query."""
        print(f"    [MEMORY RECALL] Searching Mem0 for: {query[:30]}...")
        results = self.memory.search(query, filters={"user_id": user_id})
        
        # Newer mem0 versions return {"results": [...]}, unwrap if needed
        if isinstance(results, dict) and "results" in results:
            results = results["results"]
        
        if not results:
            return []
        
        # Extract just the text from the Mem0 result objects
        memories = []
        for r in results:
            if isinstance(r, dict):
                memories.append(r.get('memory', ''))
            elif isinstance(r, str):
                memories.append(r)
        return memories

    def clear(self, user_id: str = "default_user"):
        """Wipes memory for the user."""
        self.memory.delete_all(user_id=user_id)