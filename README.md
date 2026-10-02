# FAA N-Number Monitor

[![Python Tests](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml)

A Python-based monitoring system that tracks changes in FAA aircraft N-number reservation data.

The monitor downloads FAA Releasable Aircraft data, stores reservation snapshots in SQLite, compares releases, identifies N-numbers that disappear from the reservation list, cross-references them against registered aircraft, maintains a persistent watch list, generates reports, and sends Discord notifications for meaningful changes.

The project is designed for unattended operation while maintaining logs, database backups, restore capabilities, and persistent run history for troubleshooting and verification.

---

## Features

- Downloads FAA Releasable Aircraft data
- Validates downloaded FAA ZIP archives before processing
- Verifies required FAA data files
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
- Sends Discord notifications for meaningful watch-list changes
- Automatically splits large Discord notifications
- Prevents Discord delivery failures from crashing FAA processing
- Sends Discord alerts when the monitor fails
- Maintains structured application logs
- Stores persistent monitor execution history
- Tracks successful and failed monitor runs
- Records snapshot dates and data-change information
- Records new and resolved flag counts
- Provides status and historical run inspection
- Automatically backs up SQLite before monitor processing
- Uses SQLite's backup API for safe database backups
- Retains the 14 most recent database backups
- Automatically removes older backups
- Validates backups before restoration
- Creates an emergency backup before restoring a database
- Supports database recovery from the command line
- Supports unattended execution through Windows Task Scheduler
- Includes an automated pytest test suite
- Uses GitHub Actions for continuous integration

---

## How It Works

The core monitoring pipeline is:

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
Load FAA Data
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
Cross-Reference Registered Aircraft
        /                 \
       /                   \
Registered             Not Registered
    |                       |
    v                       v
Resolved               Flag for Review
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

Each execution is also recorded in SQLite so unattended runs can be inspected later.

---

## Monitor Startup Flow

A normal monitor execution protects the existing application state before processing new FAA data.

```text
Monitor Starts
      |
      v
Initialize Database
      |
      v
Create SQLite Backup
      |
      v
Clean Old Backups
      |
      v
Create RUNNING History Record
      |
      v
Download FAA Data
      |
      v
Process Snapshot
      |
      +------------------+
      |                  |
      v                  v
   SUCCESS             FAILED
      |                  |
      v                  v
Record Results       Record Error
```

This creates a recovery point before a normal monitor run modifies persistent data.

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
│   ├── notifications.py
│   └── ...
|
├── data/
│   ├── backups/
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

Some generated directories and files may not exist until the application has run.

---

## Requirements

- Python 3
- Internet access to retrieve FAA data
- SQLite
- Discord webhook for notifications

Install project dependencies with:

```bash
pip install -r requirements.txt
```

Run commands from the root directory of the repository.

---

# Running the Monitor

## Normal Monitor Run

```bash
python -m app.main
```

A normal run performs:

```text
Database initialization
        |
        v
Database backup
        |
        v
Backup retention cleanup
        |
        v
Run-history creation
        |
        v
FAA download
        |
        v
Dataset validation
        |
        v
Snapshot processing
        |
        v
Reservation comparison
        |
        v
Watch-list processing
        |
        v
Report generation
        |
        v
Notifications
        |
        v
Run-history completion
```

---

# Command-Line Usage

## Monitor Status

Display the current monitor state without downloading new FAA data:

```bash
python -m app.main --status
```

Status information includes:

- Stored snapshots
- Latest snapshot
- Active flags
- Registered resolutions
- Returned resolutions
- Latest monitor execution
- Data-change information
- New and resolved flag counts

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

---

## Monitor Run History

Display the 10 most recent monitor executions:

```bash
python -m app.main --history
```

Specify the number of runs:

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
- Success/failure status
- FAA snapshot date
- Whether FAA data changed
- New flags
- Resolved flags
- Failure information

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

---

## List Database Backups

Display available database backups:

```bash
python -m app.main --backups
```

Backups are displayed newest first and assigned a number.

Example:

```text
Database Backups
----------------
1. nnumber_monitor_2026-10-01_17-30-00.db (20,480 bytes)
2. nnumber_monitor_2026-10-01_16-55-23.db (20,480 bytes)
3. nnumber_monitor_2026-10-01_16-20-41.db (20,480 bytes)
```

The backup number can then be used with the restore command.

---

## Restore a Database Backup

First list available backups:

```bash
python -m app.main --backups
```

Then select the backup to restore:

```bash
python -m app.main --restore-backup 2
```

The restore system:

```text
Selected Backup
      |
      v
Verify Backup Exists
      |
      v
SQLite Integrity Check
      |
      v
Create Emergency Backup
of Current Live Database
      |
      v
Restore Selected Backup
      |
      v
Live Database Replaced
```

An invalid backup number is rejected without modifying the live database.

A missing or invalid SQLite backup is also rejected before restoration begins.

---

## Run Without Routine Notifications

```bash
python -m app.main --no-notify
```

This suppresses routine watch-list Discord notifications.

Operational failure alerts remain available so unexpected monitor failures can still be reported.

---

## Test Discord Notifications

```bash
python -m app.main --test-notification
```

This sends a clearly labeled test notification and exits without processing FAA data.

---

## CLI Help

```bash
python -m app.main --help
```

---

# Watch-List Logic

When an N-number disappears from the FAA reservation data, the monitor checks whether the N-number appears in registered aircraft data.

### Registered

If the N-number is now associated with a registered aircraft, it is treated as a registration resolution.

```text
RESERVED
   |
   v
Removed
   |
   v
Registered Aircraft
   |
   v
REGISTERED
```

### Unexplained Removal

If the N-number is not registered, it can be added to the active watch list.

```text
RESERVED
   |
   v
Removed
   |
   v
Not Registered
   |
   v
FLAGGED
```

### Future Resolution

Flagged N-numbers continue to be checked during later FAA releases.

They can eventually become:

```text
REGISTERED
```

if associated with an aircraft, or:

```text
RETURNED
```

if they reappear in the reservation data.

Otherwise they remain:

```text
FLAGGED
```

---

# Discord Notifications

Discord notifications are intended for meaningful watch-list activity rather than every routine execution.

Notifications may be generated when:

- New N-numbers are flagged
- Flagged N-numbers become registered
- Flagged N-numbers return to the reservation list
- The monitor encounters an operational failure

Large notifications are automatically divided into smaller messages to remain within safe Discord message limits.

Discord delivery errors are isolated from FAA processing. A notification failure therefore does not automatically cause an otherwise successful monitor run to be classified as failed.

## Configuration

The webhook is stored using the environment variable:

```text
DISCORD_WEBHOOK_URL
```

Webhook URLs and tokens should never be committed to the repository.

Verify the configured webhook with:

```bash
python -m app.main --test-notification
```

---

# Reports

The monitor generates CSV reports containing watch-list and FAA release information.

Reports can include:

- Active flagged N-numbers
- Resolved N-numbers
- Newly flagged N-numbers
- Registration resolutions
- Returned reservation resolutions
- Release-specific changes

Generated reports are stored in the project's report directory.

---

# Database

The project uses SQLite for persistent application state.

Stored information includes:

- Reservation snapshots
- Full FAA reservation snapshots
- Flagged N-numbers
- Resolution status
- Monitor execution history

---

## Monitor Run History

Monitor execution records can contain:

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

A normal execution begins as:

```text
RUNNING
```

and is later updated to:

```text
SUCCESS
```

or:

```text
FAILED
```

Failed executions can store the associated error message.

This allows unattended scheduled executions to be verified later.

---

# Database Backups

Before normal FAA processing begins, the application creates a backup of the current SQLite database.

Backups are stored under:

```text
data/backups/
```

Example:

```text
nnumber_monitor_2026-10-01_16-55-23.db
```

The backup process uses SQLite's built-in backup API rather than directly copying an active database file.

## Backup Retention

The monitor retains the **14 most recent database backups**.

```text
Newest backup      KEEP
       |
       v
...
       |
       v
Backup #14         KEEP
Backup #15         DELETE
Backup #16         DELETE
...
```

Older backups are automatically removed.

If no database exists yet, backup creation safely returns without preventing application startup.

---

# Database Recovery

Backups can be restored using the command-line recovery tools.

Before restoration, the selected backup is checked using SQLite's integrity-check functionality.

If validation fails:

```text
Validation Failure
       |
       v
Restore Aborted
       |
       v
Live Database Untouched
```

If validation succeeds, the current live database is first backed up.

```text
Current Live Database
         |
         v
Emergency Backup
         |
         v
Selected Backup Restored
         |
         v
New Live Database
```

The emergency backup preserves the database state immediately before restoration.

This provides a rollback point if the selected restore is not the desired state.

---

# Logging

Application activity is written to:

```text
logs/nnumber_monitor.log
```

Logged activity can include:

- Monitor startup
- Database backup creation
- Backup cleanup
- FAA snapshot detection
- Watch-list summaries
- Release changes
- Report generation
- Discord delivery failures
- Monitor crashes
- Successful monitor completion

---

# Automated Scheduling

The monitor can run unattended through Windows Task Scheduler.

Example configuration:

```text
Program/script:
C:\path\to\nnumber-monitor\.venv\Scripts\python.exe

Arguments:
-m app.main

Start in:
C:\path\to\nnumber-monitor
```

Useful Task Scheduler options include:

- Run whether the user is logged on or not
- Wake the computer to run the task
- Run the task as soon as possible after a scheduled start is missed

After an unattended execution, monitor history can be checked with:

```bash
python -m app.main --history 5
```

This provides an application-level record that the scheduled execution actually occurred.

---

# Testing

Run the complete test suite with:

```bash
python -m pytest -v
```

The project currently includes:

```text
50 passed
```

## Test Coverage

Automated tests cover functionality including:

- Database initialization
- Reservation snapshots
- Duplicate snapshot protection
- Flag creation
- Flag resolution
- FAA download handling
- Download retry behavior
- FAA ZIP validation
- Logging
- Discord notifications
- Notification controls
- Large Discord message splitting
- Discord failure isolation
- CLI status output
- Monitor run creation
- Successful run completion
- Failed run completion
- Failure recording
- Latest-run retrieval
- Run-history retrieval
- Run-history limits
- SQLite backup creation
- Backup data integrity
- Automatic backup retention
- Backup startup integration
- Missing-database backup handling
- Backup discovery
- Backup CLI output
- Empty backup handling
- SQLite backup validation
- Corrupt backup rejection
- Database restoration
- Emergency pre-restore backup creation
- Restore backup selection
- Invalid restore selection protection

---

# Continuous Integration

GitHub Actions automatically runs the pytest suite when changes are pushed to the repository.

[![Python Tests](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Daisypup666/nnumber-monitor/actions/workflows/tests.yml)

The workflow follows the general process:

```text
Push / Pull Request
        |
        v
GitHub Actions
        |
        v
Create Test Environment
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

This helps detect regressions as the monitor evolves.

---

# Reliability

The project includes multiple safeguards for unattended operation:

- FAA download retries
- HTTP error handling
- FAA ZIP validation
- Dataset archiving
- Duplicate snapshot protection
- Persistent SQLite state
- Automatic database backups
- SQLite-safe backup creation
- Backup retention
- Old-backup cleanup
- Backup integrity validation
- Corrupt backup rejection
- Emergency pre-restore backups
- Safe database restoration
- Structured application logging
- Discord failure notifications
- Discord message-size handling
- Notification failure isolation
- Successful and failed run tracking
- Persistent failure information
- Automated pytest coverage
- GitHub Actions continuous integration

---

# Development Status

This project is under active development.

Current functionality focuses on:

- FAA dataset monitoring
- Persistent snapshot storage
- Automated release comparison
- N-number watch-list tracking
- Resolution tracking
- CSV reporting
- Discord notifications
- Scheduled execution
- Monitor run history
- Automatic database protection
- Database recovery
- Automated testing
- Continuous integration

Potential future improvements include:

- Improved N-number candidate analysis
- Historical trend analysis
- Better report summaries
- Web-based monitoring dashboard
- Always-on deployment
- Additional notification integrations
- Expanded data visualization

---

# Disclaimer

This project is an independent software project and is not affiliated with or endorsed by the Federal Aviation Administration.

FAA data should be treated according to the terms, limitations, and update schedules provided by the FAA. Monitor results should be verified against official FAA sources when used for decision-making.