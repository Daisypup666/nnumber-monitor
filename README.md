FAA N-Number Monitor
A Python application for monitoring changes in FAA aircraft N-number reservation data.
The application downloads the FAA Releasable Aircraft dataset, stores historical reservation snapshots in SQLite, detects N-numbers that disappear between FAA datasets, cross-references those numbers against registered aircraft records, and maintains a persistent watch list for unexplained reservation removals.
Overview
FAA aircraft registration data changes as N-numbers are reserved, assigned, changed, registered, or otherwise removed from the reservation dataset.
Rather than relying only on scheduled purge dates, this project compares historical FAA datasets directly.

Download FAA dataset

        ↓

Detect whether dataset changed

        ↓

Store historical reservation snapshot

        ↓

Compare latest two distinct snapshots

        ↓

Identify removed N-numbers

        ↓

Retrieve last-known reservation details

        ↓

Cross-reference against MASTER.txt

        ↓

     Registered?

      /       \\

    Yes        No

     ↓          ↓

 Expected     FLAGGED

transition       ↓

              Watch List

                 ↓

        Re-check on new data

           /           \\

    REGISTERED        RETURNED

           \           /

            Resolved History

This allows the application to distinguish normal reservation-to-registration transitions from N-numbers that disappear from the reservation dataset without appearing as registered aircraft.
Current Features
- Downloads the FAA Releasable Aircraft dataset
- Validates FAA HTTP responses
- Archives FAA datasets locally
- Calculates SHA-256 hashes for dataset change detection
- Detects whether FAA data changed since the previous archive
- Parses FAA RESERVED.txt
- Parses FAA MASTER.txt
- Stores historical reservation snapshots in SQLite
- Prevents duplicate snapshot records
- Skips creation of database snapshots when FAA data is unchanged
- Maintains historical snapshot dates
- Compares the two most recent distinct reservation snapshots
- Detects N-numbers removed between snapshots
- Retrieves last-known information for removed reservations
- Cross-references removed N-numbers against registered aircraft
- Separates expected registration transitions from unexplained removals
- Stores unexplained removals in a persistent watch list
- Re-checks active watch-list records when new FAA data becomes available
- Detects when a flagged N-number later becomes registered
- Detects when a flagged N-number returns to the reservation list
- Records resolution dates
- Maintains resolved N-number history
- Prevents duplicate watch-list entries
- Displays comparison and watch-list summaries
- Includes automated database and snapshot-comparison tests
- Generates full watch-list CSV reports
- Generates per-release change CSV reports
- Builds change-only notification messages
- Sends Discord webhook notifications only when a new FAA dataset produces a watch-list change
- Safely skips Discord delivery when no webhook is configured
Monitoring Workflow
A typical comparison may look like:

Previous snapshot

2026-09-25

        ↓

Current snapshot

2026-09-26

        ↓

28 reservations removed

        ↓

Cross-reference MASTER.txt

        ↓

27 registered aircraft

1 unexplained removal

        ↓

Unexplained removal saved as FLAGGED

The flagged N-number is then checked against future FAA datasets.
If it later appears in MASTER.txt:

FLAGGED

   ↓

REGISTERED

   ↓

Resolved History

If it reappears in RESERVED.txt:

FLAGGED

   ↓

RETURNED

   ↓

Resolved History

If neither occurs, it remains on the active watch list.
Example Output

\--- Comparison Summary ---

Status: Removed reservations: 28

Status: Registered aircraft: 27

Status: Flagged for review: 1

\--- Watch List Summary ---

Active flags: 1

Resolved as registered: 0

Returned to reservations: 0

\--- Active Watch List ---

N-number: 420TW

Registrant: Example Registrant

Reservation Type: CN

Category: N_NUMBER_CHANGE

Purge Date: None

Last Observed: 2026-09-25

Detected: 2026-09-26

Status: FLAGGED

\--- Resolved History ---

No resolved flags yet.

Example values are illustrative of application behavior and should not be treated as current FAA registration information.
Handling Unchanged FAA Data
The monitor distinguishes between the date the program runs and an actual change in the FAA dataset.
For example:

Friday      Dataset A

Saturday    Dataset A

Sunday      Dataset A

Monday      Dataset B

The meaningful comparison is:

Dataset A → Dataset B

not:

Friday → Saturday → Sunday → Monday

When FAA data has not changed:
- no duplicate reservation snapshot is created
- watch-list statuses are not modified
- the latest two distinct snapshots can still be compared
- the existing Active Watch List and Resolved History remain available
This prevents weekends, holidays, or repeated program runs from creating false state changes.
FAA Data
The application uses data contained in the FAA Releasable Aircraft dataset.
RESERVED.txt
Contains N-number reservation information.
Relevant information includes:
- N-number
- registrant
- reservation type
- reservation category
- purge date
Historical copies of these records are stored in SQLite and compared between FAA releases.
MASTER.txt
Contains currently registered aircraft.
The monitor loads the registered N-numbers from MASTER.txt and uses them to determine whether a reservation that disappeared has transitioned into an aircraft registration.
Project Structure
nnumber-monitor/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── faa_downloader.py
│   ├── database.py
│   ├── reporting.py
│   └── notifications.py
│
├── tests/
│   ├── test_database.py
│   ├── test_reporting.py
│   └── test_notifications.py
│
├── data/
│   └── faa_archive/
│
├── reports/
├── .env
├── .gitignore
├── README.md
└── requirements.txt
The data/ and reports/ directories contain runtime/generated data and are excluded from version control. The .env file is also excluded because it may contain the Discord webhook URL.
Application Components
main.py
Coordinates the monitoring workflow:
- checks the FAA data source
- loads reservation and aircraft registration data
- determines the current snapshot date
- stores new snapshots
- compares historical snapshots
- identifies removed reservations
- cross-references registered aircraft
- creates watch-list entries
- updates existing flags
- displays active flags
- displays resolved history
- displays monitoring summaries
faa_downloader.py
Handles FAA data operations, including:
- FAA downloads
- ZIP archive handling
- SHA-256 hashing
- dataset change detection
- parsing RESERVED.txt
- parsing MASTER.txt
- FAA date handling
- loading registered N-numbers
database.py
Handles SQLite operations, including:
- database initialization
- historical reservation storage
- snapshot retrieval
- removed-reservation detection
- last-known reservation lookup
- watch-list storage
- duplicate flag prevention
- watch-list status updates
- resolution-date tracking
- active flag retrieval
- resolved-history retrieval
- watch-list summaries
reporting.py
Generates CSV output, including:
- a full current watch-list report
- a per-release changes report
- active and resolved flag details
- dated report filenames based on the current FAA snapshot
Generated files are written under reports/ and are ignored by Git.
notifications.py
Handles notification behavior, including:
- building messages for new flags
- building messages for resolved flags
- returning no message when nothing changed
- loading the Discord webhook from environment variables
- sending Discord webhook notifications
- safely skipping delivery when a webhook is not configured
Database
The project uses SQLite for local historical storage.
Reservation Snapshots
Historical reservation data is stored with fields similar to:

n_number

registrant

reservation_type

category

purge_date

observed_date

The historical snapshots allow the monitor to determine:
Which N-numbers existed in the previous FAA dataset but are absent from the current dataset?

Flagged N-Numbers
Unexplained removals are stored in a persistent watch-list table with fields including:

n_number

registrant

reservation_type

category

purge_date

last_observed

detected_date

status

resolved_date

Possible statuses currently include:

FLAGGED

REGISTERED

RETURNED

resolved_date remains empty while an N-number is actively flagged.
Requirements
- Python 3
- requests
- pytest
- python-dotenv
The currently tested dependency versions are listed in requirements.txt.
Creating requirements.txt
requirements.txt is a plain-text file that tells Python which external packages need to be installed for the project.
From the project root, create a file named exactly:

requirements.txt

Do not name it:

requirements.txt.txt

The file should currently contain:

requests==2.34.2
pytest==9.1.1
python-dotenv==<installed-version>

Creating it in VS Code
1. Open the project folder in VS Code.
2. Right-click the project root in Explorer.
3. Select **New File**.
4. Enter:

requirements.txt

5. Add:

requests==2.34.2
pytest==9.1.1
python-dotenv==<installed-version>

6. Save the file.
Creating it from PowerShell
From the project root, you can also run:

@"

requests==2.34.2
pytest==9.1.1
python-dotenv==<installed-version>

"@ | Set-Content requirements.txt

To view the resulting text file:

Get-Content requirements.txt

Installation
Clone the repository:

git clone https://github.com/Daisypup666/nnumber-monitor.git

cd nnumber-monitor

Create a virtual environment
Windows PowerShell:

python -m venv .venv

Activate it:

.venv\Scripts\Activate.ps1

macOS/Linux:

python3 -m venv .venv

source .venv/bin/activate

Install dependencies
With the virtual environment active:

pip install -r requirements.txt

This installs the versions of requests, pytest, and python-dotenv used by the project.
Discord Notification Setup
Discord notifications are optional. The monitor reads the webhook URL from a local .env file so the secret is not stored in source code.
Create .env in the project root:
DISCORD_WEBHOOK_URL=your_webhook_url_here
Do not commit the real webhook URL. The repository .gitignore should contain:
.env
reports/
When the webhook is configured, a Discord message is sent only when both conditions are true:
1. the FAA dataset changed, and
2. the watch list had a meaningful change, such as a new flag or a flag resolving to REGISTERED or RETURNED.
If the FAA dataset is unchanged, or the new release produces no watch-list changes, the monitor stays quiet. If no webhook is configured, Discord delivery is skipped safely.
Running the Monitor
From the project root with the virtual environment active:

python app/main.py

The monitor will:
1. Check the FAA data source.
2. Download/load the current FAA dataset.
3. Determine whether the dataset changed.
4. Parse reservation records.
5. Parse registered-aircraft records.
6. Store a new snapshot when appropriate.
7. Compare the two most recent distinct snapshots.
8. Identify removed reservations.
9. Cross-reference removed N-numbers against registered aircraft.
10. Save unexplained removals to the watch list.
11. Re-check existing flags when new FAA data becomes available.
12. Display active and resolved watch-list information.
13. Show changes for the current FAA release.
14. Generate the full watch-list CSV report.
15. Generate the per-release changes CSV report.
16. Send a Discord notification when a new FAA release produces a watch-list change.
Generated Reports
The monitor creates two CSV report types.
Full watch-list report
reports/nnumber_report_YYYY-MM-DD.csv
Contains the current active and resolved watch-list state, including N-number, registrant, reservation type, category, dates, status, and resolution date.
Release changes report
reports/nnumber_changes_YYYY-MM-DD.csv
Contains only watch-list changes associated with that FAA release, such as:
- NEW FLAG
- RESOLVED - REGISTERED
- RESOLVED - RETURNED
If there are no watch-list changes for a release, the changes report may contain only its header row. Generated reports are excluded from Git by reports/ in .gitignore.
Automated Tests
The project uses pytest.
Run all tests from the project root:

python -m pytest -v

The current test suite verifies:
- a flagged N-number can resolve as REGISTERED
- a flagged N-number can resolve as RETURNED
- duplicate watch-list entries are prevented
- removed reservations are correctly detected between snapshots
- identical snapshots do not produce false removals
- full watch-list CSV export works
- per-release changes CSV export works
- no notification is built when nothing changed
- a notification is built for a new flag
- a notification is built for a resolved flag
- Discord delivery uses the expected webhook request behavior without making a real network request during the test
- missing Discord webhook configuration safely prevents sending
A successful run currently reports:
12 passed
The percentages displayed beside individual tests are test-run progress indicators, not test scores.
Test Safety
Tests use temporary SQLite databases provided through pytest's tmp_path.
The test suite redirects:

DATABASE_PATH

to a temporary database before performing database operations.
This prevents automated tests from modifying the production database located at:

data/nnumber_monitor.db

Temporary test databases are automatically disposable.
Repository Data
Runtime files should not be committed to Git.
The repository's .gitignore excludes files such as:
- Python virtual environments
- Python cache files
- SQLite runtime databases
- downloaded FAA archives
- environment files
- editor-specific configuration
- generated CSV reports
- .env secrets such as the Discord webhook URL
FAA datasets can be downloaded again when needed and therefore do not need to be stored in the Git repository.
Planned Development
Potential future improvements include:
- JSON report generation
- automated scheduled monitoring
- additional FAA parsing tests
- structured logging
- historical statistics
- watch-list aging information
- improved archive deduplication
- command-line options
Disclaimer
This project is an independent software project and is not affiliated with or endorsed by the Federal Aviation Administration.
FAA data can change and should be verified against official FAA sources before being relied upon for registration, reservation, legal, operational, or purchasing decisions.
This project is intended for educational, research, and software-development purposes.
Author
Developed by Sierra Rode.
This project demonstrates practical experience with:
- Python
- SQLite
- HTTP data ingestion
- FAA public datasets
- ZIP-file processing
- CSV parsing
- SHA-256 change detection
- historical snapshots
- change detection
- relational database design
- set-based data comparison
- persistent state tracking
- automated testing with pytest
- virtual environments
- dependency management
- CSV report generation
- environment-variable secret management
- Discord webhook integration
- notification gating
- test mocking with pytest monkeypatch
- Git and GitHub