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
                        "description": "The first name of the employee, e.g., 'Dave' or 'Sarah'"
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
    }
]

# Map tool names to their actual Python functions
TOOL_HANDLERS = {
    "lookup_team_directory": lookup_team_directory,
    "parse_temporal_expression": parse_temporal_expression
}