# Memory Integration Architecture

## Memory Tool Choice: Mem0 + ChromaDB
For our persistent memory layer, we chose **Mem0** utilizing **ChromaDB** as the local vector storage backend.

While a raw vector database (like Chroma alone) provides semantic similarity search, it lacks temporal reasoning. If a user says "Task A is assigned to John" on Monday, and "Task A is reassigned to Sarah" on Tuesday, a raw vector database will retrieve both conflicting statements, confusing the agent. 

Mem0 solves this by acting as an intelligence layer on top of Chroma. It automatically detects contradictions, updates existing memory nodes, and handles deduplication. By configuring Mem0 to use ChromaDB locally, we get state-of-the-art episodic memory management without requiring external cloud databases or running separate Docker containers for the memory server.

## Memory Structure
Mem0 structures memory automatically by extracting facts and user preferences from our meeting note outputs. It stores these in the local `./db` directory via ChromaDB.

## Concrete Example in Action
**Iteration N (Session 1):** 
1. The agent extracts: "Dave will finish the API by Friday." 
2. The agent executes `memory_manager.save()` using Mem0.
3. Mem0 embeds and stores this fact in ChromaDB.

**Iteration N+1 (Session 2):**
1. The agent processes new meeting notes: "Dave is blocked on the API. Reassigned to Alex, due next Tuesday."
2. The agent executes `memory_manager.save()`.
3. Instead of simply appending a conflicting fact, **Mem0 recognizes the contradiction**. It automatically updates the existing memory regarding the API task ownership and deadline.
4. During the next `reason` step, when the agent queries `memory_manager.recall("Who owns the API task?")`, it receives the updated fact (Alex) without the stale context (Dave).