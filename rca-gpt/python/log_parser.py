import re
import pandas as pd
from pathlib import Path

# Define log file path (relative to project root)
log_path = Path(__file__).resolve().parent.parent / 'logs' / 'app.log'

# Check if log file exists
if not log_path.exists():
    print(f"Log file not found: {log_path}")
    exit(1)

# Regular expression to extract log parts
log_pattern = re.compile(r"\[(?P<level>\w+)\]\s+(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(?P<message>.*)")

# Container to hold parsed log entries
log_entries = []

# Read and parse each line
with open(log_path, 'r') as file:
    for line in file:
        match = log_pattern.match(line.strip())
        if match:
            log_entries.append(match.groupdict())

# Convert to DataFrame
df = pd.DataFrame(log_entries)

# Output path for structured CSV
output_path = Path(__file__).resolve().parent.parent / 'logs' / 'structured_logs.csv'
df.to_csv(output_path, index=False)

print(f"Parsed {len(df)} entries. Structured logs saved to:\n{output_path}")            