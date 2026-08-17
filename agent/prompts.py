PERCEIVE_PROMPT = """
You are an expert project manager. Parse the following meeting notes and extract potential action items.
If previous feedback is provided, update your extraction based on it.

Output strictly in JSON format matching this structure:
{
    "context": "Brief summary of the meeting",
    "action_items": [
        {
            "task_id": 1,
            "description": "...",
            "owner": "...",
            "due_date": "...",
            "status": "DRAFT"
        }
    ]
}
"""

REASON_PROMPT = """
Analyze the current observation of action items. Your goal is to ensure EVERY action item has:
1. A fully resolved owner email. (NEVER guess or invent an email. You MUST use the lookup_team_directory tool if you only have a first name).
2. A concrete YYYY-MM-DD due date (not a relative date like "tomorrow").

If data is missing or vague, you MUST formulate a tool call to resolve it.
If all items are perfectly resolved, output action: "COMPLETE".

Output strictly in JSON format matching this structure:
{
    "thought": "I see task 1 belongs to Dave. I need to look up Dave's email.",
    "action": "TOOL_CALL or COMPLETE",
    "tool_name": "name of tool if TOOL_CALL",
    "tool_args": {"arg1": "value1"}
}
"""

REFLECT_PROMPT = """
Evaluate the latest state of the action items. 
Check if all items meet the SMART criteria (Specific, assigned to an EMAIL, concrete YYYY-MM-DD deadline).

Output strictly in JSON format matching this structure:
{
    "is_done": false, 
    "quality_score": 50,
    "critique": "Task 1 has an email, but the due date is still 'next Friday'.",
    "next_instruction": "Use parse_temporal_expression to resolve 'next Friday'."
}
Set "is_done": true ONLY if all items are fully resolved with emails and concrete dates.
"""