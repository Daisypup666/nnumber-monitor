import app.notifications as notifications

def test_no_notification_when_nothing_changed():
    message = notifications.build_change_notification(
        [],
        [],
        "2026-09-29"
    )

    assert message is None


def test_notification_for_new_flag():
    new_flags = [
        (
            "123TEST",
            "TEST OWNER",
            "CN",
            "N_NUMBER_CHANGE",
            None,
            "2026-09-28",
            "2026-09-29",
            "FLAGGED",
            None
        )
    ]

    message = notifications.build_change_notification(
        new_flags,
        [],
        "2026-09-29"
    )

    assert message is not None
    assert "NEW FLAGS" in message
    assert "123TEST" in message
    assert "TEST OWNER" in message


def test_notification_for_resolved_flag():
    resolved_flags = [
        (
            "456TEST",
            "SECOND OWNER",
            "CN",
            "N_NUMBER_CHANGE",
            None,
            "2026-09-25",
            "2026-09-26",
            "REGISTERED",
            "2026-09-29"
        )
    ]

    message = notifications.build_change_notification(
        [],
        resolved_flags,
        "2026-09-29"
    )

    assert message is not None
    assert "RESOLVED FLAGS" in message
    assert "456TEST" in message
    assert "REGISTERED" in message

def test_discord_notification_sends_message(monkeypatch):
    import app.notifications as notifications

    monkeypatch.setenv(
        "DISCORD_WEBHOOK_URL",
        "https://example.com/fake-webhook"
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

    def fake_post(url, json, timeout):
        assert url == "https://example.com/fake-webhook"
        assert json == {"content": "Test notification"}
        assert timeout == 10

        return FakeResponse()

    monkeypatch.setattr(
        notifications.requests,
        "post",
        fake_post
    )

    result = notifications.send_discord_notification(
        "Test notification"
    )

    assert result is True

def test_discord_notification_without_webhook(monkeypatch):
    monkeypatch.delenv(
        "DISCORD_WEBHOOK_URL",
        raising=False
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "requests.post should not be called without a webhook"
        )

    monkeypatch.setattr(
        notifications.requests,
        "post",
        fail_if_called
    )

    result = notifications.send_discord_notification(
        "Test notification"
    )

    assert result is False

def test_build_failure_notification():
    message = notifications.build_failure_notification(
        "Unable to download FAA database"
    )

    assert message is not None
    assert "⚠️ FAA N-Number Monitor Failed" in message
    assert "Unable to download FAA database" in message 
    assert "nnumber_monitor.log" in message


def test_failure_notification_can_be_sent(monkeypatch):
    sent_messages = []

    def fake_send(message):
        sent_messages.append(message)
        return True

    monkeypatch.setattr(
        notifications,
        "send_discord_notification",
        fake_send
    )

    error = RuntimeError("Test monitor failure")

    failure_message = notifications.build_failure_notification(
        error
    )

    result = notifications.send_discord_notification(
        failure_message
    )

    assert result is True
    assert len(sent_messages) == 1
    assert "FAA N-Number Monitor Failed" in sent_messages[0]
    assert "Test monitor failure" in sent_messages[0]

