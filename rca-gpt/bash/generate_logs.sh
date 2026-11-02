#!/bin/bash

log_file="$(dirname "$0")/../logs/app.log"
levels=("INFO" "WARN" "ERROR")
messages=("Login success" "Login failed" "Timeout" "Connection refused" "Invalid token")

while true; do
    level=${levels[$RANDOM % ${#levels[@]}]}
    message=${messages[$RANDOM % ${#messages[@]}]}
    echo "[$level] $(date '+%Y-%m-%d %H:%M:%S') - $message" >> "$log_file"
    sleep 2
done

