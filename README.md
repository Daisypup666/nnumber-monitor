# FAA N-Number Monitor

A Python application for monitoring FAA aircraft N-number reservation data, tracking reservation purge dates, and maintaining historical snapshots for change detection.

## Overview

The FAA N-Number Monitor downloads current aircraft registration data from the FAA, extracts reservation information, and stores historical snapshots in a SQLite database.

The project is designed to identify N-number reservations approaching their purge date and eventually detect changes between daily FAA datasets.

## Features

- Downloads the latest FAA Releasable Aircraft database
- Validates downloaded ZIP files before processing
- Archives dated FAA datasets
- Keeps the seven most recent source archives
- Parses `RESERVED.txt` from the FAA dataset
- Stores reservation snapshots in SQLite
- Prevents duplicate daily snapshot records
- Identifies reservations with upcoming purge dates
- Categorizes reservation types
- Calculates SHA-256 hashes of downloaded datasets
- Maintains historical data for future change detection

## Project Structure

```text
nnumber-monitor/
├── app/
│   ├── main.py
│   ├── database.py
│   └── faa_downloader.py
├── data/
│   └── faa_archive/
├── .gitignore
└── README.md