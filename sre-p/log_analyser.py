# log_analyser.py
# Goal: read a log file, extract ERROR lines, count by type, print summary

import sys
from collections import defaultdict

# --- STEP 1: Read the file ---
# Accept filename from command line args (sys.argv)
# If no arg given, print usage and exit
# Open the file, read all lines into a list
def read_log(filepath):
    with open("app.log", "r") as f:
        data = []
        lines = f.readlines()


# --- STEP 2: Parse errors ---
# Loop through lines
# If line contains "ERROR", extract the error type
# Log lines look like: 2024-01-15 ERROR DatabaseTimeout: connection pool exhausted
# Split on "ERROR" → take the part after, strip it, grab first word as error_type
# Store in a dict: { "DatabaseTimeout": 3, "NullPointer": 1 }
def parse_errors(lines):
    # TODO: return a dict of { error_type: count }
    ...

# --- STEP 3: Print summary ---
# Print total lines scanned
# Print total errors found
# Print each error type and count, sorted by count descending
def print_summary(total_lines, error_counts):
    # TODO: formatted print
    ...

# --- MAIN ---
# Call read_log → call parse_errors → call print_summary
if __name__ == "__main__":
    # TODO: wire it together
    ...
