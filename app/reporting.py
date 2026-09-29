import csv
from pathlib import Path


REPORT_DIR = Path("reports")


def export_watch_list_csv(active_flags, resolved_flags, report_date):
    REPORT_DIR.mkdir(exist_ok=True)

    report_path = REPORT_DIR / f"nnumber_report_{report_date}.csv"

    with open(report_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "N-Number",
            "Registrant",
            "Reservation Type",
            "Category",
            "Purge Date",
            "Last Observed",
            "Detected Date",
            "Status",
            "Resolved Date"
        ])

        for flag in active_flags:
            writer.writerow([
                flag[0],
                flag[1],
                flag[2],
                flag[3],
                flag[4],
                flag[5],
                flag[6],
                flag[7],
                None
            ])

        for flag in resolved_flags:
            writer.writerow([
                flag[0],
                flag[1],
                flag[2],
                flag[3],
                flag[4],
                flag[5],
                flag[6],
                flag[7],
                flag[8]
            ])

    return report_path


def export_release_changes_csv(new_flags, resolved_flags, report_date):
    REPORT_DIR.mkdir(exist_ok=True)

    report_path = REPORT_DIR / f"nnumber_changes_{report_date}.csv"

    with open(report_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "N-Number",
            "Registrant",
            "Category",
            "Change",
            "Detected Date",
            "Resolved Date"
        ])

        for flag in new_flags:
            writer.writerow([
                flag[0],
                flag[1],
                flag[3],
                "NEW FLAG",
                flag[6],
                ""
            ])

        for flag in resolved_flags:
            writer.writerow([
                flag[0],
                flag[1],
                flag[3],
                f"RESOLVED - {flag[7]}",
                flag[6],
                flag[8]
            ])

    return report_path

