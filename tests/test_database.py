import app.database as database


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

