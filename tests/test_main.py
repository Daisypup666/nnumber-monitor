import app.main as main


def test_show_status(monkeypatch, capsys):

    monkeypatch.setattr(
        main,
        "initialize_database",
        lambda: None
    )

    monkeypatch.setattr(
        main,
        "get_snapshot_dates",
        lambda: [
            "2026-09-30",
            "2026-09-29",
            "2026-09-26",
        ]
    )

    monkeypatch.setattr(
        main,
        "get_flagged_n_numbers",
        lambda: [
            ("420TW",)
        ]
    )

    monkeypatch.setattr(
        main,
        "get_resolved_flags",
        lambda: []
    )

    main.show_status()

    output = capsys.readouterr().out

    assert "FAA N-Number Monitor Status" in output
    assert "Snapshots stored: 3" in output
    assert "Latest snapshot: 2026-09-30" in output
    assert "Active flags: 1" in output
    assert "Registered resolutions: 0" in output
    assert "Returned resolutions: 0" in output

def test_notifications_disabled_prevents_discord_send(
    monkeypatch
):
    discord_called = {"value": False}

    def fake_send(message):
        discord_called["value"] = True
        return True

    monkeypatch.setattr(
        main,
        "send_discord_notification",
        fake_send
    )

    result = main.send_change_notification(
        notification_message="Test notification",
        data_changed=True,
        notifications_enabled=False
    )

    assert result is False
    assert discord_called["value"] is False

def test_notifications_enabled_sends_discord(
    monkeypatch
):
    sent_messages = []

    def fake_send(message):
        sent_messages.append(message)
        return True

    monkeypatch.setattr(
        main,
        "send_discord_notification",
        fake_send
    )

    result = main.send_change_notification(
        notification_message="Test notification",
        data_changed=True,
        notifications_enabled=True
    )

    assert result is True
    assert len(sent_messages) == 1
    assert sent_messages[0] == "Test notification"


def test_test_notification_sends_discord(
    monkeypatch
):
    sent_messages = []

    def fake_send(message):
        sent_messages.append(message)
        return True

    monkeypatch.setattr(
        main,
        "send_discord_notification",
        fake_send
    )

    result = main.test_notification()

    assert result is True
    assert len(sent_messages) == 1
    assert "FAA N-Number Monitor Test" in sent_messages[0]
    assert "Discord notifications are working correctly" in sent_messages[0]

def test_discord_failure_does_not_crash_monitor(
    monkeypatch
):
    def fake_send(message):
        raise RuntimeError("Discord is unavailable")

    monkeypatch.setattr(
        main,
        "send_discord_notification",
        fake_send
    )

    result = main.send_change_notification(
        notification_message="Test notification",
        data_changed=True,
        notifications_enabled=True
    )

    assert result is False

def test_record_monitor_failure(monkeypatch):
    recorded = {}

    def fake_finish_monitor_run(**kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr(
        main,
        "finish_monitor_run",
        fake_finish_monitor_run
    )

    main.current_run_id = 42

    error = RuntimeError("FAA exploded")

    result = main.record_monitor_failure(error)

    assert result is True

    assert recorded["run_id"] == 42
    assert recorded["status"] == "FAILED"
    assert recorded["error_message"] == "FAA exploded"
    assert recorded["finished_at"] is not None

    assert main.current_run_id is None

def test_show_history(monkeypatch, capsys):
    monkeypatch.setattr(
        main,
        "initialize_database",
        lambda: None
    )

    fake_runs = [
        {
            "id": 2,
            "started_at": "2026-10-02 03:00:00",
            "finished_at": "2026-10-02 03:00:08",
            "status": "SUCCESS",
            "snapshot_date": "2026-10-02",
            "data_changed": 1,
            "new_flags": 2,
            "resolved_flags": 1,
            "error_message": None
        },
        {
            "id": 1,
            "started_at": "2026-10-01 03:00:00",
            "finished_at": "2026-10-01 03:00:05",
            "status": "FAILED",
            "snapshot_date": None,
            "data_changed": None,
            "new_flags": 0,
            "resolved_flags": 0,
            "error_message": "FAA server unavailable"
        }
    ]

    monkeypatch.setattr(
        main,
        "get_monitor_run_history",
        lambda limit=10: fake_runs
    )

    main.show_history()

    output = capsys.readouterr().out

    assert "Recent Monitor Runs" in output

    assert "Run #2 - SUCCESS" in output
    assert "FAA snapshot: 2026-10-02" in output
    assert "Data changed: Yes" in output
    assert "New flags: 2 | Resolved: 1" in output

    assert "Run #1 - FAILED" in output
    assert "Error: FAA server unavailable" in output

def test_show_history_respects_limit(
    monkeypatch,
    capsys
):
    requested_limits = []

    def fake_get_history(limit=10):
        requested_limits.append(limit)
        return []

    monkeypatch.setattr(
        main,
        "initialize_database",
        lambda: None
    )

    monkeypatch.setattr(
        main,
        "get_monitor_run_history",
        fake_get_history
    )

    main.show_history(5)

    capsys.readouterr()

    assert requested_limits == [5]

def test_prepare_database_backup(monkeypatch):
    backup_calls = []
    cleanup_calls = []

    def fake_backup_database():
        backup_calls.append(True)
        return "data/backups/test_backup.db"

    def fake_cleanup_database_backups(keep):
        cleanup_calls.append(keep)
        return 0

    monkeypatch.setattr(
        main,
        "backup_database",
        fake_backup_database
    )

    monkeypatch.setattr(
        main,
        "cleanup_database_backups",
        fake_cleanup_database_backups
    )

    result = main.prepare_database_backup()

    assert result == "data/backups/test_backup.db"
    assert len(backup_calls) == 1
    assert cleanup_calls == [14]

def test_prepare_database_backup_no_database(
    monkeypatch
):
    cleanup_called = []

    def fake_backup_database():
        return None

    def fake_cleanup_database_backups(keep):
        cleanup_called.append(keep)
        return 0

    monkeypatch.setattr(
        main,
        "backup_database",
        fake_backup_database
    )

    monkeypatch.setattr(
        main,
        "cleanup_database_backups",
        fake_cleanup_database_backups
    )

    result = main.prepare_database_backup()

    assert result is None
    assert cleanup_called == []

