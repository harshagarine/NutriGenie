#!/bin/bash
# Cleanup script to kill processes on agent ports

echo "🧹 Cleaning up agent processes..."

# Kill processes on ports 8000-8003
for port in 8000 8001 8002 8003; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "  Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
    else
        echo "  Port $port is free"
    fi
done

echo "✅ Cleanup complete!"
