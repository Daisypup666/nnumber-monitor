# FAA N-Number Monitor

[Keep your existing Python Tests / GitHub Actions badge here]

A Python-based monitoring system that tracks changes in FAA aircraft N-number reservation data.

The monitor downloads the FAA Releasable Aircraft database, stores reservation snapshots in SQLite, compares releases, identifies N-numbers that disappear from the reservation list, cross-references them against registered aircraft, maintains a watch list, generates reports, and sends Discord notifications for relevant changes.

The project is designed to run automatically on a schedule while maintaining logs and persistent run history for troubleshooting and verification.

---

## Features

- Downloads FAA Releasable Aircraft data
- Validates downloaded FAA ZIP archives before processing
- Verifies required `RESERVED.txt` and `MASTER.txt` files
- Retries failed FAA downloads
- Archives FAA datasets for comparison
- Detects changes between FAA releases
- Stores reservation snapshots in SQLite
- Detects N-numbers removed from the FAA reservation list
- Cross-references removed reservations against registered aircraft
- Flags unexplained reservation removals for review
- Maintains an active N-number watch list
- Tracks N-numbers that later become registered
- Tracks N-numbers that return to the reservation list
- Maintains resolution history
- Generates CSV watch-list reports
- Generates per-release change reports
- Sends Discord notifications for watch-list changes
- Automatically splits large Discord notifications into safe message sizes
- Prevents Discord delivery failures from crashing the FAA processing job
- Sends Discord failure alerts for monitor crashes
- Maintains application logs
- Stores persistent monitor execution history in SQLite
- Tracks successful and failed monitor runs
- Records snapshot date and data-change information for each run
- Records new and resolved flag counts for each run
- Provides command-line status and history tools
- Supports unattended execution through Windows Task Scheduler
- Includes an automated pytest test suite
- Uses GitHub Actions for continuous integration

---

## How It Works

The monitor follows this general pipeline:

```text
FAA Releasable Aircraft Database
            |
            v
Download and Validate ZIP
            |
            v
Archive FAA Dataset
            |
            v
Load RESERVED.txt + MASTER.txt
            |
            v
Store Reservation Snapshot
            |
            v
Compare Current vs Previous Snapshot
            |
            v
Find Removed N-Numbers
            |
            v
Cross-Reference MASTER.txt
        /           \
       /             \
Registered       Not Registered
    |                 |
    v                 v
Resolved         Flag for Review
                      |
                      v
                 Active Watch List
                      |
            +---------+---------+
            |                   |
            v                   v
      Becomes Registered   Returns to RESERVED
            |                   |
            +---------+---------+
                      |
                      v
               Resolution History
```

Each monitor execution is also recorded in SQLite so scheduled runs can be inspected later.

---

## Project Structure

```text
nnumber-monitor/
|
├── .github/
│   └── workflows/
│       └── tests.yml
|
├── app/
│   ├── main.py
│   ├── database.py
│   ├── faa_downloader.py
│   ├── notifications.py
│   ├── logger.py
│   └── ...
|
├── data/
│   ├── faa_archive/
│   └── nnumber_monitor.db
|
├── logs/
│   └── nnumber_monitor.log
|
├── reports/
│   └── ...
|
├── tests/
│   └── ...
|
├── README.md
├── requirements.txt
└── ...
```

Some generated directories or files may not exist until the application has been run.

---

## Requirements

- Python 3
- Internet access to retrieve FAA data
- SQLite
- Discord webhook (optional, for notifications)

Install project dependencies with:

```bash
pip install -r requirements.txt
```

---

## Running the Monitor

The application uses Python package-style execution.

Run commands from the root of the repository.

### Normal Monitor Run

```bash
python -m app.main
```

This performs the normal monitoring workflow, including:

- FAA data download
- ZIP validation
- Snapshot processing
- Database updates
- Reservation comparison
- Watch-list updates
- CSV report generation
- Logging
- Discord notifications when applicable
- Monitor run-history recording

---

## Command-Line Usage

### View Monitor Status

Display the current monitor state without downloading new FAA data:

```bash
python -m app.main --status
```

Status information includes snapshot information, active and resolved watch-list counts, and information about the latest recorded monitor execution.

Example:

```text
FAA N-Number Monitor Status
---------------------------
Snapshots stored: 5
Latest snapshot: 2026-10-01

Active flags: 1
Registered resolutions: 2
Returned resolutions: 0

Last Monitor Run
----------------
Started: 2026-10-01 15:20:03
Finished: 2026-10-01 15:20:08
Status: SUCCESS
FAA snapshot: 2026-10-01
Data changed: No
New flags: 0
Resolved flags: 0
```

### View Monitor Run History

Display the 10 most recent monitor executions:

```bash
python -m app.main --history
```

Specify the number of runs to display:

```bash
python -m app.main --history 5
```

or:

```bash
python -m app.main --history 20
```

Run history can include:

- Run ID
- Start time
- Finish time
- Success or failure status
- FAA snapshot date
- Whether FAA data changed
- New flag count
- Resolved flag count
- Error information for failed runs

Example:

```text
Recent Monitor Runs
-------------------

Run #5 - SUCCESS
Started: 2026-10-01 15:20:03
Finished: 2026-10-01 15:20:08
FAA snapshot: 2026-10-01
Data changed: No
New flags: 0 | Resolved: 0

Run #4 - FAILED
Started: 2026-10-01 03:00:02
Finished: 2026-10-01 03:00:08
New flags: 0 | Resolved: 0
Error: FAA server unavailable
```

### Run Without Routine Discord Notifications

```bash
python -m app.main --no-notify
```

This runs the complete monitor while suppressing routine watch-list Discord notifications.

Operational failure alerts remain enabled so unexpected monitor failures can still be reported.

### Test Discord Notifications

```bash
python -m app.main --test-notification
```

This sends a clearly labeled test message to the configured Discord webhook and exits without processing FAA data.

### View CLI Help

```bash
python -m app.main --help
```

---

## Watch-List Logic

When an N-number disappears from `RESERVED.txt`, the monitor checks whether that N-number appears in the registered aircraft data.

If the N-number is registered, the removal is treated as a registered aircraft rather than an unexplained disappearance.

If the N-number is not registered, it can be added to the active watch list for continued monitoring.

On future FAA releases, active flags are checked again.

A flagged N-number can eventually be resolved as:

```text
REGISTERED
```

if it appears as a registered aircraft, or:

```text
RETURNED
```

if it appears in the reservation list again.

Otherwise, it remains:

```text
FLAGGED
```

---

## Discord Notifications

Discord notifications are intended for meaningful watch-list activity rather than every routine monitor execution.

Routine notifications may be generated when watch-list changes are detected, such as new flags or resolutions.

The monitor also supports operational failure notifications when the application encounters an unexpected error.

Large notifications are automatically split into multiple Discord messages to remain within Discord message-size limits.

A Discord delivery failure is logged without causing an otherwise successful FAA processing run to be treated as failed.

The Discord webhook should be stored in an environment variable:

```text
DISCORD_WEBHOOK_URL
```

Do not commit webhook URLs or tokens to the repository.

---

## Reports

The monitor generates CSV reports containing current watch-list information and changes associated with FAA releases.

Reports include:

- Active flagged N-numbers
- Resolved N-numbers
- New flags
- Resolution information
- Release-specific changes

Generated reports are stored in the project's report directory.

---

## Database

The project uses SQLite for persistent state.

The database stores information such as:

- FAA reservation snapshots
- Full FAA reservation snapshots
- Flagged N-numbers
- Resolution status
- Monitor execution history

Monitor history records can include:

```text
id
started_at
finished_at
status
snapshot_date
data_changed
new_flags
resolved_flags
error_message
```

This makes it possible to verify whether unattended monitor executions actually occurred and whether they completed successfully.

---

## Logging

Application activity is written to:

```text
logs/nnumber_monitor.log
```

Logging provides additional information for troubleshooting scheduled or unattended executions.

Examples of logged events include:

- Monitor startup
- FAA snapshot detection
- Watch-list summaries
- Release changes
- Report generation
- Discord delivery failures
- Monitor crashes
- Successful monitor completion

---

## Automated Scheduling

The monitor can run unattended through Windows Task Scheduler.

The application should be executed using package-style execution.

Example configuration:

```text
Program/script:
C:\path\to\nnumber-monitor\.venv\Scripts\python.exe

Arguments:
-m app.main

Start in:
C:\path\to\nnumber-monitor
```

For unattended execution, Task Scheduler can be configured to:

- Run whether the user is logged on or not
- Wake the computer to run the task
- Run the task as soon as possible after a scheduled start is missed

The current project is designed to support a daily scheduled monitor run.

Run history can then be checked with:

```bash
python -m app.main --history 5
```

---

## Testing

Run the complete automated test suite with:

```bash
python -m pytest -v
```

The project currently includes **36 automated tests** covering functionality such as:

- Database operations
- Reservation snapshots
- Flag creation
- Flag resolution
- FAA download handling
- Retry behavior
- FAA ZIP validation
- Logging
- Discord notifications
- Large Discord message splitting
- Discord failure isolation
- CLI status output
- Notification controls
- Monitor run creation
- Successful run completion
- Failed run completion
- Latest-run retrieval
- Run-history retrieval
- Run-history limits

---

## Continuous Integration

GitHub Actions automatically runs the pytest suite on repository pushes and pull requests.

The workflow:

```text
Push / Pull Request
        |
        v
GitHub Actions
        |
        v
Create Ubuntu Environment
        |
        v
Install Python
        |
        v
Install Dependencies
        |
        v
Run pytest
        |
        v
Pass / Fail
```

The status badge at the top of this README reflects the current CI test status.

---

## Reliability

Several safeguards are included to make unattended monitoring safer:

- FAA download retries
- HTTP error handling
- Required-file ZIP validation
- Dataset archiving
- Duplicate snapshot protection
- Persistent SQLite state
- Structured application logging
- Discord failure notifications
- Discord message-size handling
- Isolation of notification delivery failures
- Successful and failed run-history tracking
- Automated pytest coverage
- GitHub Actions CI

---

## Development Status

This project is under active development.

Current functionality focuses on reliable FAA dataset monitoring, persistent state, automated comparison, watch-list tracking, reporting, notifications, scheduled execution, and operational history.

Potential future improvements include:

- Expanded run-history reporting
- Database backup and maintenance tools
- Additional CLI controls
- Improved report summaries
- Web-based monitoring dashboard
- Deployment to an always-on environment
- Additional notification integrations

---

## Disclaimer

This project is an independent software project and is not affiliated with or endorsed by the Federal Aviation Administration.

FAA data should be treated according to the terms, limitations, and update schedules provided by the FAA. Monitor results should be verified against official FAA sources when used for decision-making.