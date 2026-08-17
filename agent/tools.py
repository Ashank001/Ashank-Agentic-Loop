import re
import json
from datetime import datetime, timedelta

# ==========================================
# 1. Tool Implementations (Handlers)
# ==========================================

def lookup_team_directory(name: str, department: str = None) -> dict:
    """Mock database lookup for employees to resolve vague names."""
    # Simulated directory database
    mock_db = {
        "dave": {"user_id": "dave.miller@company.com", "role": "Backend Engineer"},
        "alex": {"user_id": "alex.chen@company.com", "role": "DevOps"},
        "sarah": {"user_id": "sarah.j@company.com", "role": "Product Manager"}
    }
    
    query = name.lower().strip()
    if query in mock_db:
        return {"status": "success", "data": mock_db[query]}
    return {"status": "error", "message": f"User '{name}' not found in directory."}

def parse_temporal_expression(expression: str) -> dict:
    """Converts relative time like 'next Friday' to a concrete date."""
    # In a real app, you'd use the `dateparser` library. For this mock:
    today = datetime.now()
    exp_lower = expression.lower()
    
    if "tomorrow" in exp_lower:
        target = today + timedelta(days=1)
    elif "next week" in exp_lower:
        target = today + timedelta(days=7)
    elif "friday" in exp_lower:
        target = today + timedelta(days=4) # Rough mock
    else:
        return {"status": "error", "message": "Could not parse date."}
        
    return {"status": "success", "data": {"iso_date": target.strftime("%Y-%m-%d")}}

def validate_action_item(description: str, owner: str, due_date: str) -> dict:
    """Validates that an action item meets SMART criteria.
    Checks: non-empty description, valid email owner, concrete YYYY-MM-DD date."""
    issues = []
    
    # Check description
    if not description or len(description.strip()) < 5:
        issues.append("Description is missing or too vague (must be >= 5 characters).")
    
    # Check owner is a valid email
    if not owner or not re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', owner):
        issues.append(f"Owner '{owner}' is not a valid email address.")
    
    # Check due_date is a concrete YYYY-MM-DD
    try:
        parsed = datetime.strptime(due_date, "%Y-%m-%d")
        if parsed.date() < datetime.now().date():
            issues.append(f"Due date '{due_date}' is in the past.")
    except (ValueError, TypeError):
        issues.append(f"Due date '{due_date}' is not a valid YYYY-MM-DD date.")
    
    if issues:
        return {"status": "invalid", "issues": issues}
    return {"status": "valid", "message": "Action item meets all SMART criteria."}

# ==========================================
# 2. Tool Definitions (JSON Schema for LLM)
# ==========================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_team_directory",
            "description": "Looks up an employee by first name to get their exact email address and role. Use this when a meeting note only mentions a first name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The first name of the employee, e.g., 'Ashank' or 'Priya'"
                    },
                    "department": {
                        "type": "string",
                        "description": "Optional department name to narrow down."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_temporal_expression",
            "description": "Converts a relative date expression (e.g. 'tomorrow', 'next Friday') into a concrete YYYY-MM-DD date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The relative time expression."
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_action_item",
            "description": "Validates that a single action item meets SMART criteria. Checks that the owner is a valid email, the due_date is a concrete YYYY-MM-DD format, and the description is specific enough. Returns a list of issues if validation fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The task description, e.g., 'Prepare API documentation'"
                    },
                    "owner": {
                        "type": "string",
                        "description": "The owner's email address, e.g., 'ashank.kumar@company.com'"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "The due date in YYYY-MM-DD format, e.g., '2026-08-22'"
                    }
                },
                "required": ["description", "owner", "due_date"]
            }
        }
    }
]

# Map tool names to their actual Python functions
TOOL_HANDLERS = {
    "lookup_team_directory": lookup_team_directory,
    "parse_temporal_expression": parse_temporal_expression,
    "validate_action_item": validate_action_item
}