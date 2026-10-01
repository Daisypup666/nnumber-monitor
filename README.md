# FAA N-Number Monitor

[![Python Tests](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml)


A Python-based monitoring tool that tracks changes in FAA aircraft N-number reservation data.

The application downloads the latest FAA Releasable Aircraft database, stores historical reservation snapshots in SQLite, detects N-numbers that disappear from the reservation list, cross-references them against registered aircraft, maintains a persistent watch list, generates CSV reports, sends Discord notifications for meaningful watch-list changes, and records runtime activity in log files.

The project is designed to run manually or automatically through Windows Task Scheduler.

---

## Overview

FAA N-number reservation records can change between database releases.

An N-number disappearing from `RESERVED.txt` does not necessarily mean that it has become available. It may have:

- Been assigned to a registered aircraft
- Returned to the reservation system
- Changed status
- Disappeared from the reservation dataset for another reason

This project maintains historical FAA snapshots so those changes can be detected and investigated automatically.

The basic monitoring workflow is:

```text
Download FAA database
        ↓
Determine FAA snapshot date
        ↓
Check whether snapshot was already processed
        ↓
Load RESERVED.txt and MASTER.txt
        ↓
Store new reservation snapshot in SQLite
        ↓
Compare current and previous snapshots
        ↓
Detect removed N-numbers
        ↓
Cross-reference registered aircraft
        ↓
Maintain persistent watch list
        ↓
Detect resolved flags
        ↓
Generate CSV reports
        ↓
Build Discord notification
        ↓
Write runtime log
```

---

## Current Features

### FAA Data Retrieval

- Downloads the FAA Releasable Aircraft database
- Verifies successful FAA HTTP responses
- Extracts reservation and aircraft registration information
- Archives FAA releases for historical comparison
- Retains a configurable number of historical archives

### Reservation Snapshot Tracking

FAA reservation records are stored in SQLite with their associated snapshot date.

This creates a historical record that allows the application to compare FAA releases over time.

Stored information includes:

- N-number
- Registrant
- Reservation type
- Category
- Purge date
- Snapshot date

### Previously Processed Snapshot Detection

Before processing a release, the application checks whether its snapshot date already exists in the database.

If the snapshot has already been processed:

- The reservation snapshot is not saved again
- Watch-list resolution processing is skipped
- Historical snapshot comparison is skipped
- Duplicate Discord notifications are prevented

This allows the monitor to run repeatedly without repeatedly processing the same FAA release.

### Snapshot Comparison

When a genuinely new snapshot is detected, the application compares the newest stored reservation snapshot with the previous snapshot.

Example:

```text
2026-09-29
      ↓
2026-09-30
```

The monitor identifies N-numbers that existed in the previous snapshot but no longer exist in the current reservation data.

### Registered Aircraft Cross-Reference

Removed reservations are checked against FAA registered-aircraft data from `MASTER.txt`.

A removed reservation that now exists as a registered aircraft is classified as:

```text
REGISTERED AIRCRAFT
```

A removed reservation that cannot be explained by aircraft registration is classified as:

```text
FLAG FOR REVIEW
```

### Persistent Watch List

Unexplained removals are stored in a persistent watch list.

A watch-list entry contains information such as:

```text
N-number
Registrant
Reservation Type
Category
Purge Date
Last Observed
Detected Date
Status
Resolved Date
```

Active flags remain in the database across future runs.

### Watch-List Resolution

Each new FAA release checks active flags again.

An active flag can transition to:

```text
FLAGGED
    ↓
REGISTERED
```

if the N-number appears in the FAA registered-aircraft database.

Or:

```text
FLAGGED
    ↓
RETURNED
```

if the N-number reappears in the FAA reservation list.

Resolved entries remain available in the historical database.

### Duplicate Flag Protection

The database prevents the same active N-number from being repeatedly inserted into the watch list.

This keeps the watch list focused on unique unresolved events.

---

## FAA Change Detection

The monitor includes content-based hashing for files inside FAA ZIP archives.

Rather than relying only on the hash of the entire ZIP container, the application can hash the actual FAA data files:

```text
RESERVED.txt
MASTER.txt
```

This is useful because ZIP-level differences do not necessarily represent meaningful changes to the underlying FAA data.

The monitor can therefore distinguish between:

```text
Different ZIP packaging
        ↓
Same underlying FAA data
```

and:

```text
FAA data contents changed
        ↓
Meaningful release difference
```

Historical snapshot dates stored in SQLite provide an additional safeguard against processing the same release more than once.

---

## CSV Reporting

The monitor automatically generates CSV reports in:

```text
reports/
```

The reports directory is excluded from Git because these files are generated at runtime.

### Watch-List Report

A full watch-list report is generated for the current snapshot.

Example:

```text
reports/nnumber_report_2026-09-30.csv
```

It contains the current active and resolved watch-list state.

### Release Changes Report

The application also generates a report containing changes associated with the current release.

Example:

```text
reports/nnumber_changes_2026-09-30.csv
```

This report records newly detected and newly resolved watch-list entries for that release.

---

## Discord Notifications

The monitor can send Discord notifications through a webhook.

Notifications are generated for meaningful watch-list changes such as:

- New flagged N-numbers
- Flags resolved as registered aircraft
- Flags returned to the reservation system

The notification system is intentionally gated.

```text
FAA snapshot already processed
        ↓
No Discord notification
```

```text
New FAA snapshot
        +
No watch-list changes
        ↓
No Discord notification
```

```text
New FAA snapshot
        +
Watch-list changes
        ↓
Send Discord notification
```

This prevents repeated scheduled runs from spamming the Discord channel.

---

## Runtime Logging

Application activity is written to:

```text
logs/nnumber_monitor.log
```

The log records information such as:

- Monitor startup
- FAA snapshot date
- New or previously processed snapshots
- Watch-list totals
- New flags
- Resolved flags
- CSV report generation
- Successful completion
- Application errors

Example:

```text
2026-09-30 12:55:38 | INFO | N-number Monitor started
2026-09-30 12:55:40 | INFO | New FAA snapshot detected: 2026-09-30
2026-09-30 12:55:46 | INFO | FAA snapshot date: 2026-09-30
2026-09-30 12:55:47 | INFO | Watch list summary - Active: 1 | Registered: 0 | Returned: 0
2026-09-30 12:55:47 | INFO | Release changes - New flags: 0 | Resolved: 0
2026-09-30 12:55:47 | INFO | N-number Monitor completed successfully
```

The `logs/` directory is excluded from Git.

---

## Automated Scheduling

The monitor can run unattended using Windows Task Scheduler.

A scheduled task can launch the Python interpreter inside the project's virtual environment:

```text
C:\path\to\Nnumber-monitor\.venv\Scripts\python.exe
```

with:

```text
app\main.py
```

as the argument.

The task's working directory should be the project root:

```text
C:\path\to\Nnumber-monitor
```

This is important because the application uses project-relative paths for:

```text
data/
reports/
logs/
.env
```

Recommended Task Scheduler settings include:

- Run daily
- Allow task to be run on demand
- Run as soon as possible after a missed scheduled start
- Do not start a second instance if the monitor is already running

A successful scheduled execution should report:

```text
0x0
```

in Windows Task Scheduler.

---

## Project Structure

```text
Nnumber-monitor/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── faa_downloader.py
│   ├── reporting.py
│   ├── notifications.py
│   └── logger.py
│
├── tests/
│   ├── test_database.py
│   ├── test_faa_downloader.py
│   ├── test_logger.py
│   ├── test_notifications.py
│   └── test_reporting.py
│
├── data/
│   └── faa_archive/
│
├── reports/
├── logs/
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

Generated runtime files are intentionally excluded from Git.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Daisypup666/nnumber-monitor.git
cd nnumber-monitor
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should then see:

```text
(.venv)
```

at the beginning of your terminal prompt.

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

The project uses packages including:

```text
requests
python-dotenv
pytest
```

---

## Environment Configuration

Discord credentials are stored in a local `.env` file.

Create:

```text
.env
```

in the project root.

Add:

```text
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

Do not commit the actual webhook URL.

The `.env` file is excluded through `.gitignore`.

---

## Running the Monitor

From the project root with the virtual environment activated:

```powershell
python app/main.py
```

The application will:

1. Initialize the SQLite database
2. Download/check the current FAA database
3. Determine the FAA snapshot date
4. Check whether that snapshot has already been processed
5. Load reservation and registered-aircraft data
6. Update active watch-list entries when appropriate
7. Store a new reservation snapshot when appropriate
8. Compare new and previous snapshots
9. Detect removed reservations
10. Cross-reference registered aircraft
11. Update the persistent watch list
12. Generate CSV reports
13. Build notifications
14. Send Discord notifications when appropriate
15. Record the run in the application log

---

## Example Output

A new release may produce output similar to:

```text
N-number Monitor
Starting application...

FAA response status: 200

Total FAA reservation records: 127740

New FAA snapshot saved.

Snapshot dates:
['2026-09-30', '2026-09-29', '2026-09-26']

comparing: 2026-09-29 -> 2026-09-30

N-numbers removed from the reservation list: 28

--- Comparison Summary ---
Status: Removed reservations: 28
Status: Registered aircraft: 28
Status: Flagged for review: 0

--- Watch List Summary ---
Active flags: 1
Resolved as registered: 0
Returned to reservations: 0

--- Changes This Release ---
No watch list changes this release.

CSV report saved: reports/nnumber_report_2026-09-30.csv
Changes CSV saved: reports/nnumber_changes_2026-09-30.csv
```

If the snapshot was already processed:

```text
FAA snapshot 2026-09-30 has already been processed.

Skipping comparison for already processed snapshot 2026-09-30.
```

---

## Database

The application uses SQLite for persistent state.

The database is stored under:

```text
data/
```

Database files are excluded from Git.

### Reservation Snapshots

Historical reservation records allow the monitor to compare FAA releases.

Conceptually:

```text
reservation_snapshots

id
n_number
registrant
reservation_type
category
purge_date
snapshot_date
```

### Flagged N-Numbers

The persistent watch list stores unexplained removals and their eventual resolution.

Conceptually:

```text
flagged_n_numbers

id
n_number
registrant
reservation_type
category
purge_date
last_observed
detected_date
status
resolved_date
```

Possible statuses include:

```text
FLAGGED
REGISTERED
RETURNED
```

## Command-Line Usage

Run the FAA N-Number Monitor normally:

```bash
python -m app.main

Display the current monitor status without downloading new FAA data:
python -m app.main --status

Run the full monitor while suppressing routine Discord notifications:
python -m app.main --no-notify

The --no-notify option suppresses routine watch-list notifications. Operational failure alerts remain enabled so unexpected monitor failures can still be reported.
---

## Automated Testing

The project currently includes **16 automated tests**.

The test suite covers behavior including:

- Resolving a flag as registered
- Resolving a flag as returned
- Duplicate flag prevention
- Removed-reservation detection
- No removals when snapshots match
- Existing snapshot detection
- Watch-list CSV generation
- Release-change CSV generation
- Notification generation when a new flag appears
- Notification generation when a flag resolves
- No notification when nothing changes
- Discord webhook sending behavior
- Safe handling when no webhook is configured
- Runtime logging
- Identical FAA ZIP-member content hashing
- Changed FAA ZIP-member content detection

Run all tests with:

```powershell
python -m pytest -v
```

Expected result:

```text
16 passed
```

The tests use temporary data where appropriate so the production FAA database and reports are not modified.

---

## Git-Ignored Runtime Data

Runtime and local-environment files should not be committed.

The project ignores files/directories such as:

```gitignore
# SQLite database
data/*.db
data/*.db-shm
data/*.db-wal

# Reports
reports/

# Runtime logs
logs/

# Environment / secrets
.env

# Virtual environment
.venv/

# Python cache
__pycache__/
*.pyc

# VS Code
.vscode/
```

FAA archive handling can be adjusted depending on whether historical source ZIP files should remain local or be preserved elsewhere.

---

## Development Workflow

A typical development cycle is:

```text
Make code change
      ↓
Run monitor manually
      ↓
Run automated tests
      ↓
Inspect generated output/logs
      ↓
git status
      ↓
Commit
      ↓
Push to GitHub
```

Before committing:

```powershell
python -m pytest -v
```

Then inspect:

```powershell
git status
```

This helps ensure runtime files, logs, reports, secrets, and local databases are not accidentally committed.

---

## Architecture

The project separates responsibilities across several modules.

### `main.py`

Coordinates the monitoring workflow.

Responsibilities include:

- Application startup
- Snapshot processing
- Watch-list lifecycle
- Historical comparisons
- Reporting
- Notifications
- Runtime logging

### `faa_downloader.py`

Handles FAA data retrieval and parsing.

Responsibilities include:

- FAA downloads
- Archive handling
- Snapshot-date extraction
- Reservation loading
- Registered-aircraft loading
- File hashing
- FAA content-change detection

### `database.py`

Handles SQLite persistence.

Responsibilities include:

- Database initialization
- Reservation snapshots
- Snapshot history
- Removed-reservation queries
- Watch-list persistence
- Flag status updates
- Watch-list summaries

### `reporting.py`

Handles CSV generation.

Responsibilities include:

- Full watch-list reports
- Per-release change reports

### `notifications.py`

Handles notification generation and delivery.

Responsibilities include:

- Building human-readable change notifications
- Reading Discord configuration from the environment
- Sending Discord webhook messages
- Safely handling missing webhook configuration

### `logger.py`

Handles application logging.

Responsibilities include:

- Creating the runtime log directory
- Configuring the application logger
- Formatting timestamps and log levels
- Writing monitor activity to disk

---

## Design Goals

This project is intended to demonstrate more than a one-off data script.

The architecture focuses on:

- Historical state tracking
- Persistent SQLite storage
- Automated data retrieval
- Change detection
- Data normalization
- State transitions
- Reporting
- Notifications
- Scheduled execution
- Runtime observability
- Automated testing
- Safe secret management
- Modular Python design

---

## Future Development

Potential future improvements include:

### Notification Improvements

- Rich Discord embeds
- More detailed new-flag information
- Failure notifications
- Notification retry handling

### Monitoring Improvements

- Better distinction between FAA release changes and previously processed releases
- More detailed release metadata
- Additional validation of downloaded FAA files
- More robust handling of FAA download failures

### Reporting Improvements

- Summary statistics
- Historical trend reports
- JSON exports
- HTML reports

### Application Improvements

- Command-line arguments
- Configurable archive retention
- Configurable report directory
- Configurable logging level
- Structured application configuration

### Deployment

- GitHub Actions or another automated execution environment
- Containerized deployment
- Cloud-hosted scheduled execution
- Health monitoring

### User Interface

A future dashboard could provide:

- Active watch-list entries
- Resolved N-numbers
- Snapshot history
- Search by N-number
- Historical status changes
- Report downloads

---

## Security

Sensitive configuration such as Discord webhook URLs must not be committed to the repository.

Secrets are stored locally using:

```text
.env
```

and excluded through:

```gitignore
.env
```

If a webhook URL is ever accidentally committed to Git, the webhook should be revoked and replaced.

---

## Data Source

This project operates on publicly released FAA aircraft registration and N-number reservation data.

The monitor is an independent software project and is not affiliated with or endorsed by the FAA.

---

## Status

Current development milestone:

```text
FAA download                    COMPLETE
Reservation parsing             COMPLETE
SQLite snapshot storage         COMPLETE
Historical comparison           COMPLETE
Registered-aircraft lookup      COMPLETE
Persistent watch list           COMPLETE
Flag resolution                 COMPLETE
CSV reporting                   COMPLETE
Discord notifications           COMPLETE
Runtime logging                 COMPLETE
Windows scheduled execution     COMPLETE
Duplicate snapshot protection   COMPLETE
FAA content hashing             COMPLETE
Automated testing               16 PASSING
```

The project is now capable of operating as a scheduled local monitoring service while maintaining historical state, reports, notifications, and runtime logs.