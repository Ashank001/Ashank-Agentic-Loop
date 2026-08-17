import json
import time
from datetime import datetime

class AgentLogger:
    def __init__(self):
        self.start_times = {}

    def start_step(self, step_name: str):
        self.start_times[step_name] = time.time()

    def log_step(self, iteration: int, step_name: str, input_data: any, output_data: any, error: str = None):
        """Logs the step as a structured JSON line."""
        latency = round((time.time() - self.start_times.get(step_name, time.time())) * 1000, 2)
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "iteration": iteration,
            "step": step_name,
            "input_summary": str(input_data)[:200] + ("..." if len(str(input_data)) > 200 else ""),
            "output_summary": str(output_data)[:200] + ("..." if len(str(output_data)) > 200 else ""),
            "latency_ms": latency
        }
        if error:
            log_entry["error"] = error
            
        # Print structured JSON to stdout
        print(json.dumps(log_entry))

# Global instance
agent_logger = AgentLogger()