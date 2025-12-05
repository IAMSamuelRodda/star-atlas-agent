# Benchmark Results Storage

Results are stored as JSONL (JSON Lines) files for easy appending and querying.

## File Structure

```
benchmarks/
├── README.md           # This file
├── results/            # Raw benchmark results (JSONL)
│   ├── streaming.jsonl # Streaming stress test results
│   ├── warmup.jsonl    # Component warmup results
│   └── e2e.jsonl       # End-to-end latency results
└── reports/            # Generated reports (future)
```

## Schema

See `schema.json` for the full JSON Schema definition.

## Querying Results

```bash
# View all results for a model
cat results/streaming.jsonl | jq 'select(.parameters.model == "qwen2.5:7b")'

# Get average first_token_ms across all runs
cat results/streaming.jsonl | jq -s '[.[].results.first_token_ms] | add / length'

# Filter by date
cat results/streaming.jsonl | jq 'select(.timestamp >= "2025-12-05")'
```

## Adding Results

Results are automatically appended by test scripts with `--save-results` flag:

```bash
python test_streaming_stress.py --model qwen2.5:7b --save-results
python test_warmup.py --save-results
```
