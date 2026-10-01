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