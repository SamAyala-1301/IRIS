#!/bin/bash

log_file="$(dirname "$0")/../logs/app.log"
alert_file="$(dirname "$0")/../logs/alert.log"
threshold=3

# Count ERRORs in the last 50 lines
error_count=$(tail -n 50 "$log_file" | grep -c "ERROR")

# If too many errors, write to alert log
if [ "$error_count" -gt "$threshold" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ALERT: $error_count errors found in last 50 lines" >> "$alert_file"
fi
