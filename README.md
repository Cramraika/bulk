# bulk

Fire a large number of HTTP requests from a CSV file, with retries, adaptive rate limiting, resume
after interruption, a REST API, and a SQLite record of every request.

[![License](https://img.shields.io/github/license/Cramraika/bulk)](./LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker)](./Dockerfile)
[![Stars](https://img.shields.io/github/stars/Cramraika/bulk?style=social)](https://github.com/Cramraika/bulk/stargazers)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/Cramraika?logo=github&label=Sponsor)](https://github.com/sponsors/Cramraika)

## What it does

`webhook_trigger.py` reads a CSV where each row describes one HTTP request — at minimum a target
URL, optionally a method, JSON body, and headers — and sends them through a thread pool. Around that
core loop it provides:

- **Retries** with exponential backoff, honouring the `Retry-After` header.
- **Adaptive rate limiting** that slows down as the error rate climbs.
- **Resume**: progress is checkpointed to a marker file, so an interrupted run continues from the
  last saved row instead of re-sending everything.
- **A REST API** on a built-in HTTP server, so runs can be triggered and inspected remotely.
- **A directory watcher** that picks up CSV files dropped into a watched folder and processes them
  automatically, archiving or rejecting each file afterwards.
- **A SQLite database** recording every request and every job.
- **Slack and email notifications** for job start, progress, and completion.

Everything lives in one Python file with no web framework — the HTTP server is
`http.server` from the standard library.

### Who it is for

Anyone with a list of HTTP calls to make and a reason to care whether they succeeded: backfilling
webhooks after an outage, replaying events into a downstream system, bulk-notifying an integration,
or driving a one-off migration through someone's API.

### Who it is not for

It is a single-process batch runner, not a distributed queue. There is no clustering, no scheduler
daemon, and no multi-tenancy.

## Requirements

- Python 3 with the packages in `requirements.txt` (`requests`, `tqdm`, `PyYAML`, `watchdog`,
  `python-dateutil`, and `sentry-sdk` for optional error reporting).
- Optionally Docker and Docker Compose — a `Dockerfile` and `docker-compose.yml` are included.

## Install

```bash
git clone https://github.com/Cramraika/bulk.git
cd bulk
pip install -r requirements.txt
```

Generate a starter config and inspect the interactive mode:

```bash
python webhook_trigger.py --create-config
python webhook_trigger.py --interactive
```

Note that `--create-config` and `--interactive` are special-cased as the **first argument only**.
They are not argparse flags, so `python webhook_trigger.py data.csv --interactive` silently ignores
the flag and runs a normal CSV job.

### Docker

```bash
mkdir -p data/{csv/{processed,duplicates,rejected},reports,logs,backups}
cp .env.example .env      # then edit .env
docker-compose up -d
docker-compose logs -f
```

The container defaults assume the `/app/data` layout above — `DATABASE_PATH` defaults to
`/app/data/webhook_results.db` and `WATCH_PATHS` to `/app/data/csv`. Override both if you run
outside Docker.

## Usage

```
python webhook_trigger.py <csv_file> [options]
```

The positional argument accepts a path to a CSV file, or one of two keywords:

| Value | Behaviour |
|---|---|
| a file path | Process that CSV |
| `auto` | Auto-discover CSV files to process |
| `watchdog` | Run in directory-monitoring mode |

### Options

These are the complete argparse flags, as defined in the source:

| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--config` | `-c` | path | — | Configuration file (YAML or JSON) |
| `--job-name` | `-n` | string | — | Custom job name |
| `--skip-rows` | `-s` | int | `0` | Number of rows to skip |
| `--keep-alive` | `-k` | flag | off | Keep the process running with the watchdog |
| `--workers` | `-w` | int | — | Number of parallel workers |
| `--rate-limit` | `-r` | float | — | Base rate limit, in requests per second |
| `--verbose` | `-v` | flag | off | Verbose logging |
| `--dry-run` | `-d` | flag | off | Validate the CSV without sending requests |
| `--watchdog` | | flag | off | Enable file monitoring |
| `--no-watchdog` | | flag | off | Disable file monitoring |
| `--health-port` | | int | `8000` | Port for the health-check server |

When `--workers` or `--rate-limit` are omitted, the corresponding environment variable is used.

### Examples

```bash
# Validate a file without sending anything
python webhook_trigger.py webhooks.csv --dry-run -v

# Run with explicit concurrency and pacing
python webhook_trigger.py webhooks.csv \
  --job-name "October backfill" \
  --workers 10 \
  --rate-limit 5.0

# Resume: re-running the same file continues from the last checkpoint
python webhook_trigger.py large_file.csv

# Watch a directory and stay running
python webhook_trigger.py watchdog --keep-alive
```

## CSV format

Only **`webhook_url`** is required by default. The required set is configurable through
`CSV_REQUIRED_COLUMNS` (comma-separated). Header names are normalised, so casing and surrounding
whitespace do not matter.

| Column | Required | Notes |
|---|---|---|
| `webhook_url` | yes | Target URL. Validated before sending. |
| `method` | no | HTTP method. **Defaults to `GET`** when the column is absent or empty. |
| `payload` | no | Request body, as JSON. |
| `header`, `headers`, or `headers_sent` | no | Custom headers, as JSON. Any of the three names is accepted. |
| `name` | no | Friendly identifier, recorded with the result. |
| `group` | no | Category or grouping label. |

The `GET` default is easy to trip over: if you intend to POST, include a `method` column.

```csv
webhook_url,method,payload,header,name,group
https://api.example.com/hook1,POST,"{""user"":""john""}","{""Content-Type"":""application/json""}",User Create,users
https://api.example.com/hook2,POST,"{""text"":""Alert""}","{""Content-Type"":""application/json""}",Alert,alerts
```

Header count and payload size are capped internally, and oversized values are truncated.

## Configuration

Configuration comes from environment variables, optionally overlaid by a YAML or JSON file passed
with `--config`. The source reads roughly 79 variables; the most commonly used are below, with their
**actual defaults from the code**.

### Throughput

```bash
MAX_WORKERS=3                    # concurrent worker threads
BASE_RATE_LIMIT=3.0              # requests per second (not a delay)
MAX_RATE_LIMIT=5.0               # ceiling used by adaptive rate adjustment
MAX_RETRIES=3                    # retry attempts per request
REQUEST_TIMEOUT=30               # per-request timeout, seconds
CSV_CHUNK_SIZE=1000              # rows read per chunk
```

`BASE_RATE_LIMIT` is expressed in **requests per second**. The rate limiter converts it to a
minimum interval between request starts (`1 / rate`); it is deliberately approximate pacing rather
than a strict token bucket, and concurrency is bounded by `MAX_WORKERS`.

### Resume

```bash
RESUME_ENABLED=true
RESUME_CHECKPOINT_INTERVAL=100   # save progress every N rows
RESUME_MAX_AGE_DAYS=7            # ignore checkpoints older than this
```

Checkpoints are keyed by a hash of the input file, so editing the CSV invalidates the checkpoint and
the job starts over rather than resuming at a row that no longer means the same thing.

### API server

```bash
HEALTH_PORT=8000
WEBHOOK_AUTH_TOKEN=              # if set, required as a Bearer token
WEBHOOK_RATE_LIMIT=60            # per-IP requests per minute
```

Leaving `WEBHOOK_AUTH_TOKEN` unset leaves the API unauthenticated. Set it before exposing the port
anywhere but localhost.

### Storage and files

```bash
DATABASE_PATH=/app/data/webhook_results.db
WATCH_PATHS=/app/data/csv
REPORT_KEEP=200                  # job reports retained before pruning
```

### Notifications and error reporting

```bash
SLACK_NOTIFICATIONS=true
SLACK_WEBHOOK_URL=
SLACK_NOTIFY_PROGRESS=true
SLACK_PROGRESS_EVERY_N=25

EMAIL_NOTIFICATIONS=true
EMAIL_SMTP_SERVER=
EMAIL_SMTP_PORT=
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_RECIPIENTS=

SENTRY_DSN=                      # optional; Sentry is initialised only if set
```

See `.env.example` and `config.yaml` for the full surface.

## REST API

The built-in server exposes these routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Index |
| GET | `/health` | Health check |
| GET | `/status` | Active job status |
| GET | `/jobs` | Job history |
| GET | `/jobs/{job_id}` | Job detail (also `/errors` and `/report` sub-paths) |
| GET | `/metrics` | System metrics |
| GET | `/config` | Effective configuration |
| GET | `/resume/stats` | All resume markers |
| POST | `/trigger` | Start a job for one CSV file |
| POST | `/trigger/batch` | Start jobs for several CSV files |
| POST | `/resume/status` | Resume state for a file |
| POST | `/resume/clear` | Clear a file's resume marker |

```bash
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WEBHOOK_AUTH_TOKEN" \
  -d '{"csv_file": "/app/data/csv/webhooks.csv", "job_name": "API job", "resume": true}'

curl http://localhost:8000/health
curl http://localhost:8000/jobs
```

## Data model

SQLite, at `DATABASE_PATH`. Five tables are created on startup:

| Table | Contents |
|---|---|
| `webhook_results` | One row per request: `job_id`, `url`, `method`, `status`, `status_code`, `response_time`, `timestamp`, `attempt`, `error_message`, `response_preview`, `request_size`, `response_size`, `headers_sent` |
| `job_history` | One row per job: `job_id`, `job_name`, `csv_file`, `total_requests`, `successful_requests`, `failed_requests`, `start_time`, `end_time`, `duration_seconds`, `status`, `triggered_by`, `average_response_time` |
| `scheduled_jobs` | Job schedule definitions |
| `file_tracking` | Per-file hash, status, and processing history |
| `system_metrics` | Time-series metric samples |

```sql
SELECT job_name,
       total_requests,
       successful_requests,
       ROUND(successful_requests * 100.0 / total_requests, 2) AS success_rate
FROM job_history
WHERE start_time >= datetime('now', '-7 days')
ORDER BY start_time DESC;
```

## Directory layout

```
data/
├── csv/            # watched for incoming files
│   ├── processed/  # successfully processed
│   ├── duplicates/ # rejected by file-hash deduplication
│   └── rejected/   # failed validation
├── reports/        # JSON job reports and resume markers
├── logs/
├── backups/        # database backups
└── webhook_results.db
```

## Limitations and gotchas

- **`method` defaults to `GET`.** Rows without an explicit `method` are sent as GET, which is rarely
  what a webhook backfill wants.
- **The API is unauthenticated unless `WEBHOOK_AUTH_TOKEN` is set.** There is per-IP rate limiting,
  but no auth by default.
- **`--interactive` and `--create-config` only work as the first argument.** Anywhere else they are
  ignored without warning.
- **Single process, single node.** Concurrency is a thread pool inside one process. Scaling out means
  splitting the CSV yourself.
- **Rate limiting is approximate.** It paces request starts and adapts to error rates; it is not a
  strict token bucket and does not guarantee a hard ceiling.
- **Editing a CSV invalidates its resume checkpoint** (checkpoints are hash-keyed), and checkpoints
  older than `RESUME_MAX_AGE_DAYS` are ignored.
- **Defaults assume the Docker layout.** `DATABASE_PATH` and `WATCH_PATHS` point at `/app/data`; set
  them explicitly when running locally.
- **`fleet_egress_client.py` is an optional integration** with a service that is not publicly
  available. It stays inert unless `FLEET_WEBHOOK_EGRESS_URL` is set, and can be ignored.

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) and
[SECURITY.md](./SECURITY.md).

## License

MIT © 2026 Vagary Labs LLP. See [LICENSE](./LICENSE).

A Vagary Labs project.
