import csv
import app.reporting as reporting


def test_watch_list_csv_export(tmp_path):
    # Send reports to a temporary folder
    reporting.REPORT_DIR = tmp_path

    active_flags = [
        (
            "420TW",
            "TEST OWNER",
            "CN",
            "N_NUMBER_CHANGE",
            None,
            "2026-09-25",
            "2026-09-26",
            "FLAGGED"
        )
    ]

    resolved_flags = []

    report_path = reporting.export_watch_list_csv(
        active_flags,
        resolved_flags,
        "2026-09-29"
    )

    assert report_path.exists()

    with open(report_path, newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    # Header + one N-number
    assert len(rows) == 2

    assert rows[0][0] == "N-Number"
    assert rows[1][0] == "420TW"
    assert rows[1][1] == "TEST OWNER"
    assert rows[1][7] == "FLAGGED"

def test_release_changes_csv_export(tmp_path):
    reporting.REPORT_DIR = tmp_path

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

    report_path = reporting.export_release_changes_csv(
        new_flags,
        resolved_flags,
        "2026-09-29"
    )

    assert report_path.exists()

    with open(report_path, newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert len(rows) == 3

    assert rows[1][0] == "123TEST"
    assert rows[1][3] == "NEW FLAG"

    assert rows[2][0] == "456TEST"
    assert rows[2][3] == "RESOLVED - REGISTERED"
    assert rows[2][5] == "2026-09-29"