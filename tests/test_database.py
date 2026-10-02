import app.database as database
import sqlite3
import os
import pytest

def test_flag_can_be_resolved_as_registered(tmp_path):
    # Use a temporary database instead of the real one
    test_db = tmp_path / "test_nnumber_monitor.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db
    

    # Create the database tables
    database.initialize_database()

    # Create a test flag
    database.save_flagged_n_number(
        n_number="123TEST",
        registrant="TEST OWNER",
        reservation_type="TEST",
        category="TEST_CATEGORY",
        purge_date=None,
        last_observed="2026-09-25",
        detected_date="2026-09-26"
    )

    # Resolve the flag
    database.update_flag_status(
        "123TEST",
        "REGISTERED",
        "2026-09-29"
    )

    # It should no longer be an active flag
    active_flags = database.get_flagged_n_numbers()

    assert active_flags == []

    # It should now appear in resolved history
    resolved_flags = database.get_resolved_flags()

    assert len(resolved_flags) == 1
    assert resolved_flags[0][0] == "123TEST"
    assert resolved_flags[0][7] == "REGISTERED"
    assert resolved_flags[0][8] == "2026-09-29"

def test_flag_can_be_resolved_as_returned(tmp_path):
    # Use a temporary database
    test_db = tmp_path / "test_nnumber_monitor.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    # Create a test flag
    database.save_flagged_n_number(
        n_number="456TEST",
        registrant="TEST OWNER",
        reservation_type="TEST",
        category="TEST_CATEGORY",
        purge_date=None,
        last_observed="2026-09-25",
        detected_date="2026-09-26"
    )

    # Simulate the N-number returning to RESERVED
    database.update_flag_status(
        "456TEST",
        "RETURNED",
        "2026-09-30"
    )

    # It should no longer be active
    active_flags = database.get_flagged_n_numbers()

    assert active_flags == []

    # It should appear in resolved history
    resolved_flags = database.get_resolved_flags()

    assert len(resolved_flags) == 1
    assert resolved_flags[0][0] == "456TEST"
    assert resolved_flags[0][7] == "RETURNED"
    assert resolved_flags[0][8] == "2026-09-30"

def test_duplicate_flag_is_not_saved(tmp_path):
    test_db = tmp_path / "test_nnumber_monitor.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    # Save the exact same flag twice
    for _ in range(2):
        database.save_flagged_n_number(
            n_number="789TEST",
            registrant="TEST OWNER",
            reservation_type="TEST",
            category="TEST_CATEGORY",
            purge_date=None,
            last_observed="2026-09-25",
            detected_date="2026-09-26"
        )

    active_flags = database.get_flagged_n_numbers()

    # There should still only be one copy
    assert len(active_flags) == 1
    assert active_flags[0][0] == "789TEST"

def test_removed_reservation_is_detected(tmp_path):
    test_db = tmp_path / "test_nnumber_monitor.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    previous_reservations = [
        {
            "n_number": "111AA",
            "registrant": "OWNER ONE",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        },
        {
            "n_number": "222BB",
            "registrant": "OWNER TWO",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        },
        {
            "n_number": "333CC",
            "registrant": "OWNER THREE",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        }
    ]

    current_reservations = [
        {
            "n_number": "111AA",
            "registrant": "OWNER ONE",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        },
        {
            "n_number": "333CC",
            "registrant": "OWNER THREE",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        }
    ]

    database.save_reservations(
        previous_reservations,
        "2026-09-25"
    )

    database.save_reservations(
        current_reservations,
        "2026-09-26"
    )

    removed = database.get_removed_reservations(
        "2026-09-26",
        "2026-09-25"
    )

    assert removed == ["222BB"]

def test_no_removed_reservations_when_snapshots_match(tmp_path):
    test_db = tmp_path / "test_nnumber_monitor.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    reservations = [
        {
            "n_number": "111AA",
            "registrant": "OWNER ONE",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        },
        {
            "n_number": "222BB",
            "registrant": "OWNER TWO",
            "reservation_type": "TEST",
            "category": "TEST",
            "purge_date": None
        }
    ]

    database.save_reservations(
        reservations,
        "2026-09-25"
    )

    database.save_reservations(
        reservations,
        "2026-09-26"
    )

    removed = database.get_removed_reservations(
        "2026-09-26",
        "2026-09-25"
    )

    assert removed == []

def test_existing_snapshot_date_is_detected():
    database.save_reservations(
        [
            {
                "n_number": "123TEST",
                "registrant": "TEST OWNER",
                "reservation_type": "CN",
                "category": "TEST_CATEGORY",
                "purge_date": None,
            }
        ],
        "2026-09-30"
    )

    snapshot_dates = database.get_snapshot_dates()


def test_start_monitor_run(tmp_path):
    test_db = tmp_path / "test_monitor_runs.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    run_id = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    assert run_id == 1

    connection = sqlite3.connect(test_db)

    row = connection.execute(
        """
        SELECT started_at, status
        FROM monitor_runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()

    connection.close()

    assert row == (
        "2026-10-01 03:00:00",
        "RUNNING"
    )


def test_finish_monitor_run_success(tmp_path):
    test_db = tmp_path / "test_monitor_runs.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    run_id = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    database.finish_monitor_run(
        run_id=run_id,
        finished_at="2026-10-01 03:00:08",
        status="SUCCESS",
        snapshot_date="2026-10-01",
        data_changed=True,
        new_flags=2,
        resolved_flags=1
    )

    connection = sqlite3.connect(test_db)

    row = connection.execute(
        """
        SELECT
            started_at,
            finished_at,
            status,
            snapshot_date,
            data_changed,
            new_flags,
            resolved_flags,
            error_message
        FROM monitor_runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()

    connection.close()

    assert row == (
        "2026-10-01 03:00:00",
        "2026-10-01 03:00:08",
        "SUCCESS",
        "2026-10-01",
        1,
        2,
        1,
        None
    )

def test_finish_monitor_run_failure(tmp_path):
    test_db = tmp_path / "test_monitor_runs.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    run_id = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    database.finish_monitor_run(
        run_id=run_id,
        finished_at="2026-10-01 03:00:05",
        status="FAILED",
        error_message="FAA server unavailable"
    )

    connection = sqlite3.connect(test_db)

    row = connection.execute(
        """
        SELECT
            status,
            finished_at,
            snapshot_date,
            data_changed,
            new_flags,
            resolved_flags,
            error_message
        FROM monitor_runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()

    connection.close()

    assert row == (
        "FAILED",
        "2026-10-01 03:00:05",
        None,
        None,
        0,
        0,
        "FAA server unavailable"
    )

def test_get_latest_monitor_run(tmp_path):
    test_db = tmp_path / "test_monitor_runs.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    first_run = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    database.finish_monitor_run(
        run_id=first_run,
        finished_at="2026-10-01 03:00:05",
        status="SUCCESS",
        snapshot_date="2026-10-01",
        data_changed=False
    )

    second_run = database.start_monitor_run(
        "2026-10-02 03:00:00"
    )

    database.finish_monitor_run(
        run_id=second_run,
        finished_at="2026-10-02 03:00:07",
        status="SUCCESS",
        snapshot_date="2026-10-02",
        data_changed=True,
        new_flags=3,
        resolved_flags=1
    )

    latest = database.get_latest_monitor_run()

    assert latest is not None
    assert latest["id"] == second_run
    assert latest["started_at"] == "2026-10-02 03:00:00"
    assert latest["finished_at"] == "2026-10-02 03:00:07"
    assert latest["status"] == "SUCCESS"
    assert latest["snapshot_date"] == "2026-10-02"
    assert latest["data_changed"] == 1
    assert latest["new_flags"] == 3
    assert latest["resolved_flags"] == 1
    assert latest["error_message"] is None

def test_get_monitor_run_history(tmp_path):
    test_db = tmp_path / "test_monitor_runs.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db

    database.initialize_database()

    first_run = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    database.finish_monitor_run(
        run_id=first_run,
        finished_at="2026-10-01 03:00:05",
        status="SUCCESS"
    )

    second_run = database.start_monitor_run(
        "2026-10-02 03:00:00"
    )

    database.finish_monitor_run(
        run_id=second_run,
        finished_at="2026-10-02 03:00:06",
        status="SUCCESS"
    )

    third_run = database.start_monitor_run(
        "2026-10-03 03:00:00"
    )

    database.finish_monitor_run(
        run_id=third_run,
        finished_at="2026-10-03 03:00:07",
        status="FAILED",
        error_message="Test failure"
    )

    history = database.get_monitor_run_history(
        limit=2
    )

    assert len(history) == 2

    # Newest should come first
    assert history[0]["id"] == third_run
    assert history[0]["status"] == "FAILED"
    assert history[0]["error_message"] == "Test failure"

    assert history[1]["id"] == second_run
    assert history[1]["status"] == "SUCCESS"

def test_backup_database(tmp_path):
    test_db = tmp_path / "test_nnumber_monitor.db"
    backup_dir = tmp_path / "backups"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = test_db
    database.BACKUP_DIR = backup_dir

    database.initialize_database()

    # Put some real data into the database
    run_id = database.start_monitor_run(
        "2026-10-01 03:00:00"
    )

    database.finish_monitor_run(
        run_id=run_id,
        finished_at="2026-10-01 03:00:05",
        status="SUCCESS",
        snapshot_date="2026-10-01",
        data_changed=True,
        new_flags=2,
        resolved_flags=1
    )

    # Create the backup
    backup_path = database.backup_database()

    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.parent == backup_dir

    # Open the BACKUP, not the original
    connection = sqlite3.connect(backup_path)

    row = connection.execute(
        """
        SELECT
            status,
            snapshot_date,
            data_changed,
            new_flags,
            resolved_flags
        FROM monitor_runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()

    connection.close()

    assert row == (
        "SUCCESS",
        "2026-10-01",
        1,
        2,
        1
    )

def test_cleanup_database_backups(tmp_path):
    backup_dir = tmp_path / "backups"

    database.BACKUP_DIR = backup_dir

    backup_dir.mkdir()

    # Create 20 fake backup files
    for number in range(20):
        backup_path = (
            backup_dir /
            f"nnumber_monitor_{number:02d}.db"
        )

        backup_path.write_text(
            f"backup {number}"
        )

        # Give each file a different modification time
        timestamp = 1000 + number

        os.utime(
            backup_path,
            (timestamp, timestamp)
        )

    removed = database.cleanup_database_backups(
        keep=14
    )

    remaining = list(
        backup_dir.glob("nnumber_monitor_*.db")
    )

    assert removed == 6
    assert len(remaining) == 14

    remaining_names = {
        path.name
        for path in remaining
    }

    # Newest backup should remain
    assert "nnumber_monitor_19.db" in remaining_names

    # Oldest backup should have been removed
    assert "nnumber_monitor_00.db" not in remaining_names

def test_get_database_backups_newest_first(
    tmp_path
):
    backup_dir = tmp_path / "backups"

    database.BACKUP_DIR = backup_dir

    backup_dir.mkdir()

    for number in range(3):
        backup_path = (
            backup_dir /
            f"nnumber_monitor_{number}.db"
        )

        backup_path.write_text(
            f"backup {number}"
        )

        timestamp = 1000 + number

        os.utime(
            backup_path,
            (timestamp, timestamp)
        )

    backups = database.get_database_backups()

    assert len(backups) == 3

    assert backups[0].name == (
        "nnumber_monitor_2.db"
    )

    assert backups[1].name == (
        "nnumber_monitor_1.db"
    )

    assert backups[2].name == (
        "nnumber_monitor_0.db"
    )

def validate_database_backup(backup_path):
    backup_path = Path(backup_path)

    if not backup_path.exists():
        return False

    if not backup_path.is_file():
        return False

    try:
        connection = sqlite3.connect(backup_path)

        result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        connection.close()

        return (
            result is not None
            and result[0] == "ok"
        )

    except sqlite3.Error:
        return False

def test_validate_database_backup_valid(
    tmp_path
):
    backup_path = tmp_path / "valid_backup.db"

    connection = sqlite3.connect(backup_path)

    connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("hello",)
    )

    connection.commit()
    connection.close()

    assert (
        database.validate_database_backup(
            backup_path
        )
        is True
    )

def test_validate_database_backup_invalid(
    tmp_path
):
    backup_path = tmp_path / "invalid_backup.db"

    backup_path.write_text(
        "this is definitely not sqlite"
    )

    assert (
        database.validate_database_backup(
            backup_path
        )
        is False
    )

def test_restore_database_backup(tmp_path):
    live_db = tmp_path / "live.db"
    backup_db = tmp_path / "backup.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = live_db

    # Create the current/live database.
    live_connection = sqlite3.connect(live_db)

    live_connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    live_connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("current data",)
    )

    live_connection.commit()
    live_connection.close()

    # Create the backup database containing older data.
    backup_connection = sqlite3.connect(backup_db)

    backup_connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    backup_connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("restored data",)
    )

    backup_connection.commit()
    backup_connection.close()

    result = database.restore_database_backup(
        backup_db
    )

    assert result["database_path"] == live_db
    assert result["emergency_backup"] is not None
    assert result["emergency_backup"].exists()

    # Verify the LIVE database now contains
    # the data from the backup.
    connection = sqlite3.connect(live_db)

    row = connection.execute(
        """
        SELECT value
        FROM test_data
        """
    ).fetchone()

    connection.close()

    assert row == ("restored data",)

def test_restore_database_backup_rejects_invalid(
    tmp_path
):
    live_db = tmp_path / "live.db"
    invalid_backup = tmp_path / "corrupt.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = live_db
    database.BACKUP_DIR = tmp_path / "backups"
    
    # Create a valid live database.
    connection = sqlite3.connect(live_db)

    connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("important live data",)
    )

    connection.commit()
    connection.close()

    # This is NOT a valid SQLite database.
    invalid_backup.write_text(
        "definitely not a sqlite database"
    )

    with pytest.raises(ValueError):
        database.restore_database_backup(
            invalid_backup
        )

    # Make sure the live database was untouched.
    connection = sqlite3.connect(live_db)

    row = connection.execute(
        """
        SELECT value
        FROM test_data
        """
    ).fetchone()

    connection.close()

    assert row == ("important live data",)

def test_restore_database_creates_emergency_backup(
    tmp_path
):
    live_db = tmp_path / "live.db"
    restore_db = tmp_path / "restore.db"

    database.DATA_DIR = tmp_path
    database.DATABASE_PATH = live_db
    database.BACKUP_DIR = tmp_path / "backups"

    # Create the current live database.
    connection = sqlite3.connect(live_db)

    connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("original live data",)
    )

    connection.commit()
    connection.close()

    # Create the database we want to restore.
    connection = sqlite3.connect(restore_db)

    connection.execute(
        """
        CREATE TABLE test_data (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
        """
    )

    connection.execute(
        """
        INSERT INTO test_data (value)
        VALUES (?)
        """,
        ("restored data",)
    )

    connection.commit()
    connection.close()

    result = database.restore_database_backup(
        restore_db
    )

    emergency_backup = result["emergency_backup"]

    assert emergency_backup is not None
    assert emergency_backup.exists()

    # The emergency backup should contain
    # the database state BEFORE the restore.
    connection = sqlite3.connect(
        emergency_backup
    )

    emergency_row = connection.execute(
        """
        SELECT value
        FROM test_data
        """
    ).fetchone()

    connection.close()

    assert emergency_row == (
        "original live data",
    )

    # The live database should now contain
    # the restored data.
    connection = sqlite3.connect(live_db)

    live_row = connection.execute(
        """
        SELECT value
        FROM test_data
        """
    ).fetchone()

    connection.close()

    assert live_row == (
        "restored data",
    )

