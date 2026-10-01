import os
import requests
from dotenv import load_dotenv


load_dotenv()

def build_change_notification(new_flags, resolved_flags, report_date):
    if not new_flags and not resolved_flags:
        return None

    lines = [
        f"FAA N-Number Monitor - {report_date}",
        ""
    ]

    if new_flags:
        lines.append("NEW FLAGS")

        for flag in new_flags:
            lines.append(
                f"{flag[0]} | {flag[1]} | {flag[3]}"
            )

        lines.append("")

    if resolved_flags:
        lines.append("RESOLVED FLAGS")

        for flag in resolved_flags:
            lines.append(
                f"{flag[0]} | {flag[7]} | {flag[1]}"
            )

    return "\n".join(lines).strip()

def send_discord_notification(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Discord webhook not configured.")
        return False

    response = requests.post(
        webhook_url,
        json={"content": message},
        timeout=10
    )

    response.raise_for_status()

    return True

def build_failure_notification(error):
    return(
        "⚠️ FAA N-Number Monitor Failed\n\n"
        f"Error: {error}\n\n"
        "Check logs/nnumber_monitor.log for more details."
    )