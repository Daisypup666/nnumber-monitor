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