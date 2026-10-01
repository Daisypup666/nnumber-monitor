import app.database as database
import sqlite3

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

    