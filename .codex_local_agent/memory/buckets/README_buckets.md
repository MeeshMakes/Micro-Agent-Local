# Buckets Memory Store

Append-only JSONL records live here:
- `bucket_versions.jsonl` — ordered versions of each logic bucket.
- `bucket_status.jsonl` — heartbeat/current/superseded markers per version.
- `bucket_diffs.jsonl` — unified diffs between successive versions.

Files are written by `micro_agent.py` BucketStore and must remain append-only for auditability.
