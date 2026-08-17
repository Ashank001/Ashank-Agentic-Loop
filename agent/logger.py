import json
import time
import os
from datetime import datetime

class AgentLogger:
    def __init__(self):
        self.start_times = {}
        # Ensure the logs directory exists
        self.log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "agent_execution.log")

    def start_step(self, step_name: str):
        self.start_times[step_name] = time.time()

    def log_step(self, iteration: int, step_name: str, input_data: any, output_data: any, error: str = None):
        """Logs the step as a structured JSON line to a file and stdout."""
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
            
        json_log = json.dumps(log_entry)
        
        # Write to log file only (no terminal output)
        with open(self.log_file, "a") as f:
            f.write(json_log + "\n")

# Global instance
agent_logger = AgentLogger()