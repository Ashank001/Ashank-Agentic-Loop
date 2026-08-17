# Agentic Patterns Research

## Pattern Explanations
* **Chain-of-Thought (CoT):** An prompting technique where the LLM is instructed to output its step-by-step reasoning process before arriving at a final answer. This reduces errors in logic but does not allow the agent to interact with the outside world.
* **ReAct (Reason + Act):** An interleaved framework where the agent reasons about its current state, decides on a concrete action (like calling an external tool), observes the result of that action, and then reasons again based on the new observation.
* **Reflexion:** A framework that adds a self-evaluation step to the agent loop. After generating an output or taking actions, the agent evaluates its own performance against the goal, generates a verbal critique (linguistic feedback), and uses that critique to improve its next attempt.
* **Tree of Thoughts (ToT):** A search-based reasoning approach where the LLM explores multiple different reasoning branches concurrently, evaluating the promise of each path and backtracking if a path leads to a dead end.
* **LATS (Language Agent Tree Search):** A general framework that unifies ReAct, ToT, and Reflexion. It models the agent's decision space as a Monte Carlo Tree Search (MCTS), exploring different action trajectories, simulating their outcomes, and using self-reflection to score the value of each path.

## Chosen Patterns: ReAct + Reflexion
Our core loop utilizes a hybrid of **ReAct** and **Reflexion**. 

### Why this fits the Use Case (Extracting Action Items)
Extracting action items from messy, unstructured meeting notes is inherently an iterative process of disambiguation and validation. 
1. **ReAct** is necessary because the agent cannot simply "guess" missing information. If the notes say "Dave will finish the API by next Friday," the agent must *Reason* that "Dave" is ambiguous and *Act* by calling a `lookup_team_directory` tool, and call a `parse_temporal_expression` tool to convert "next Friday" to a real date.
2. **Reflexion** is necessary for quality assurance. Once the agent compiles a draft list of action items, the `reflect` step acts as an internal auditor. It checks if every task meets strict criteria (has a clear owner, a parsed due date, and an actionable description). If the criteria are not met, the reflection step generates a critique (e.g., "Task 2 is missing a due date") and feeds it back into the loop for another iteration.