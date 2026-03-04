#!/usr/bin/env bash
set -euo pipefail

export ANTHROPIC_API_KEY=your-api-key
export DAYTONA_API_KEY=your-daytona-api-key

RUNS=1

for i in $(seq 1 $RUNS); do
    echo "========================================"
    echo "Run $i / $RUNS - Starting at $(date)"
    echo "========================================"

    uv run harbor run \
        --agent-import-path "terminus_kira.terminus_kira:TerminusKira" \
        -d "terminal-bench@2.0" \
        -m "anthropic/claude-opus-4-6" \
        -e daytona \
        --n-concurrent 50

    echo "========================================"
    echo "Run $i / $RUNS - Finished at $(date)"
    echo "========================================"
    echo ""
done

echo "All $RUNS runs completed!"
