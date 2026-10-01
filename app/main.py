from app.logger import setup_logger
logger = setup_logger()

from app.notifications import (
    build_change_notification,
    send_discord_notification,
    build_failure_notification,
)
from app.reporting import (
    export_watch_list_csv,
    export_release_changes_csv,
)
from app.database import (
    initialize_database,
    #save_candidates,
    #count_snapshots,
    #imports duplicate snapshot
    #count_duplicate_snapshots,
    save_reservations,
    count_reservation_snapshots,
    get_snapshot_dates,
    get_removed_reservations,
    get_reservation_details,
    save_flagged_n_number,
    get_flagged_n_numbers,
    update_flag_status,
    get_flag_summary,
    get_resolved_flags,
    get_flags_detected_on_date,
    get_flags_resolved_on_date,
)
from app.faa_downloader import (
    #show_data_directory,
    #list_zip_contents,
    #preview_reserved_data,
    #parse_reserved_data,
    #commented out as they are no longer
    #used only used for exploration of the zip file
    #find_upcoming_purges,
    get_snapshot_date_from_path,
    load_reservations,
    check_faa_connection,
    #preview_master_data,
    load_registered_n_numbers,
)
import argparse

#from pathlib import Path

def import_archived_snapshot(zip_path):
    reservations = load_reservations(zip_path)
    snapshot_date = get_snapshot_date_from_path(zip_path)


    #print("Importing archived snapshot:", snapshot_date)
    #print("Reservation records:", len(reservations))

    save_reservations(reservations, snapshot_date)

    #print("Archived snapshot imported.")

def show_status():
    initialize_database()

    snapshot_dates = get_snapshot_dates()

    flagged = get_flagged_n_numbers()
    resolved = get_resolved_flags()

    active_count = len(flagged)

    registered_count = sum(
        1 for flag in resolved
        if flag[7] == "REGISTERED"
    )

    returned_count = sum(
        1 for flag in resolved
        if flag[7] == "RETURNED"
    )

    print("\nFAA N-Number Monitor Status")
    print("---------------------------")

    print(f"Snapshots stored: {len(snapshot_dates)}")

    if snapshot_dates:
        print(f"Latest snapshot: {snapshot_dates[0]}")
    else:
        print("Latest snapshot: None")

    print()
    print(f"Active flags: {active_count}")
    print(f"Registered resolutions: {registered_count}")
    print(f"Returned resolutions: {returned_count}")


def send_change_notification(
    notification_message,
    data_changed,
    notifications_enabled=True
):
    if (
        notifications_enabled
        and data_changed
        and notification_message
    ):
        print("\n--- Notification ---")
        print(notification_message)

        if send_discord_notification(notification_message):
            print("Discord notification sent.")
            return True

    return False

def main(notifications_enabled=True):
    logger.info("N-number Monitor started")


    print("N-number Monitor")
    print("Starting application...")
    initialize_database()

    faa_zip_path, data_changed = check_faa_connection()

    snapshot_date = get_snapshot_date_from_path(faa_zip_path)

    existing_snapshot_dates = get_snapshot_dates()
    #print("DEBUG snapshot_date:", repr(snapshot_date))
    #print("DEBUG snapshot_date type:", type(snapshot_date))
    #print("DEBUG existing_snapshot_dates:", repr(existing_snapshot_dates))

    #if existing_snapshot_dates:
    #    print(
    #        "DEBUG stored date type:",
    #        type(existing_snapshot_dates[0])
    #    )

    #print(
    #    "DEBUG already processed comparison:",
    #    snapshot_date in existing_snapshot_dates
    #)
   # print("DEBUG snapshot_date type:", type(snapshot_date))
    #print("DEBUG existing_snapshot_dates:", repr(existing_snapshot_dates))

   # if existing_snapshot_dates:
   #     print(
   #         "DEBUG stored date type:",
   #         type(existing_snapshot_dates[0])
   #     )

   # print(
    #    "DEBUG already processed comparison:",
    #    snapshot_date in existing_snapshot_dates
    #)
    already_processed = snapshot_date in existing_snapshot_dates

    if already_processed:
        data_changed = False
        logger.info(
            "FAA snapshot %s already processed",
            snapshot_date
        )
    else:
        logger.info(
            "New FAA snapshot detected: %s",
            snapshot_date
        )



    #testing preview master data 
    #print("\nFirst 5 rows of MASTER.text:")
    #preview_master_data(faa_zip_path)


   # print("TEST: about to import Sept 25")
    #temp to ts previous dates path not getting snap shotted
    #archive_path = Path(
    #"data/faa_archive/ReleasableAircraft_2026-09-25.zip"
    #)
    #print("Archive path:", archive_path.resolve())
    #print("Archive exists:", archive_path.exists())

    #import_archived_snapshot(archive_path)

    #show_data_directory()

    #print("\nFiles inside FAA database:")
    #list_zip_contents()
    #print("\nFirst 5 rows fo RESERVED.txt:")
    #preview_reserved_data()
    #print("\nParsed reservations: ")
    #parse_reserved_data()
    #archive_dir = Path("data/faa_archive")

    #for archive_path in archive_dir.glob("*2026-09-25.zip"):
    #    print("Found archive:", archive_path)
    #    import_archived_snapshot(archive_path)




    # commented out as debug/exploation output
   # print("\nReservations purging within 30 days:") 
   
    reservations = load_reservations(faa_zip_path)
    #print("Total FAA reservation records:", len(reservations))

    registered_n_numbers = load_registered_n_numbers(faa_zip_path)
    flagged_n_numbers = get_flagged_n_numbers()
    #print("Active flagged N-numbers:", len(flagged_n_numbers))
    reserved_n_numbers = {
        reservation["n_number"]
        for reservation in reservations
    }
    if data_changed:

        for flag in flagged_n_numbers:
            n_number = flag[0]

            if n_number in registered_n_numbers:
                update_flag_status(n_number, "REGISTERED", snapshot_date)
                print(f"Watch list update: {n_number} is now registered.")

            elif n_number in reserved_n_numbers:
                update_flag_status(n_number, "RETURNED", snapshot_date)
                print(f"Watch list update: {n_number} RETURNED TO reserved")

            else:
                print(f"Watch list update: {n_number} remains FLAGGED")

            "Registered aircraft N-numbers loaded:",
            len(registered_n_numbers)
        
        print("Total FAA reservation records:", len(reservations))

   #old method:
   # snapshot_date = date.today().isoformat()
    logger.info("FAA snapshot date: %s", snapshot_date)
    #print("Snapshot date being saved:", snapshot_date)

  
    if data_changed:
        save_reservations(reservations, snapshot_date)
        print("New FAA snapshot saved. ")
    else:
        print(
            f"FAA snapshot {snapshot_date} has already been processed."
        )
   
  
    print(
        "FAA reservation snapshots stored:",
        count_reservation_snapshots() 
    )

   

    snapshot_dates = get_snapshot_dates()
    print("Snapshot dates:", snapshot_dates)
    report_date = snapshot_date

    if already_processed:
        print(
            f"Skipping comparison for already processed snapshot "
            f"{snapshot_date}."
        )

    elif len(snapshot_dates) < 2:
        print(
            "Waiting for another FAA snapshot before comparing changes."
        )

    else:
        current_date = snapshot_dates[0]
        previous_date = snapshot_dates[1]

        report_date = current_date

        removed_reservations = get_removed_reservations(
            current_date,
            previous_date
        )
        print("comparing:", previous_date, "->", current_date)
        print(
            "N-numbers removed from the reservation list:",
            len(removed_reservations)
        )
        registered_count = 0
        flagged_count = 0
        for n_number in removed_reservations:
            details = get_reservation_details(
                n_number,
                previous_date
            )
            if details:
                print("\nN_number:", details[0])
                print("Registrant:", details[1])
                print("Reservation Type:", details[2])
                print("Category:", details[3])
                print("Purge Date:", details[4])
                print("Last Date:", details[5])
                if n_number in registered_n_numbers:
                    print("Status: REGISTERED AIRCRAFT")
                    registered_count += 1
                else:
                    print("Status: FLAG FOR REVIEW")
                    flagged_count += 1

                    save_flagged_n_number(
                        n_number=details[0],
                        registrant=details[1],
                        reservation_type=details[2],
                        category=details[3],
                        purge_date=details[4],
                        last_observed=details[5],
                        detected_date=current_date
                    )

                    
        print("\n--- Comparison Sumarry --")
        print("Status: Removed reservations:", len(removed_reservations))
        print("Status: Registered aircraft:", registered_count)
        print("Status: Flagged for review:", flagged_count)

    flag_summary = get_flag_summary()
    logger.info(
        "Watch list summary - Active: %s | Registered: %s | Returned: %s",
        flag_summary.get("FLAGGED", 0),
        flag_summary.get("REGISTERED", 0),
        flag_summary.get("RETURNED", 0)
    )
    print("\n---Watch List Summary ---")
    print("Active flags:", flag_summary.get("FLAGGED", 0))
    print(
        "Resolved as registered:",
        flag_summary.get("REGISTERED", 0)
    )
    print(
        "Returned to reservations:",
        flag_summary.get("RETURNED", 0)
    )

    flagged_n_numbers = get_flagged_n_numbers()
    print("\n--- Active Watch List ---")

    if not flagged_n_numbers:
        print("No active flags.")
    else:
        for flag in flagged_n_numbers:
            print(f"\nN-number: {flag[0]}")
            print(f"Registrant: {flag[1]}")
            print(f"Reservation Type: {flag[2]}")
            print(f"Category: {flag[3]}")
            print(f"Purge Date: {flag[4]}")
            print(f"Last Observed: {flag[5]}")
            print(f"Detected: {flag[6]}")
            print(f"Status: {flag[7]}")

    resolved_flags = get_resolved_flags()

    print("\n--- Resolved History ---")

    if not resolved_flags:
        print("No resolved flags yet.")
    else:
        for flag in resolved_flags:
            print(f"\nN-number: {flag[0]}")
            print(f"Registrant: {flag[1]}")
            print(f"Category: {flag[3]}")
            print(f"Detected: {flag[6]}")
            print(f"Resolution: {flag[7]}")
            print(f"Resolved: {flag[8]}")  

    new_flags = get_flags_detected_on_date(report_date)
    resolved_this_release = get_flags_resolved_on_date(report_date)
    logger.info(
        "Release changes - New flags: %s | Resolved: %s",
        len(new_flags),
        len(resolved_this_release)
    )
    print("\n--- Changes This Release ---")

    if not new_flags and not resolved_this_release:
        print("No watch list changes this release.")

    else:
        for flag in new_flags:
            print(f"\nNEW FLAG: {flag[0]}")
            print(f"Registrant: {flag[1]}")
            print(f"Category: {flag[3]}")

        for flag in resolved_this_release:
            print(f"\nRESOLVED -> {flag[7]}: {flag[0]}")
            print(f"Registrant: {flag[1]}")
            print(f"Resolved: {flag[8]}")


    #reload current database state for the CSV report
    flagged_n_numbers = get_flagged_n_numbers()
    resolved_flags = get_resolved_flags()

    report_path = export_watch_list_csv(
        flagged_n_numbers,
        resolved_flags,
        report_date
    )

    print(f"\nCSV report saved: {report_path}")        
    changes_report_path = export_release_changes_csv(
        new_flags,
        resolved_this_release,
        report_date
    )

    print(f"Changes CSV saved: {changes_report_path}")

    notification_message = build_change_notification(
        new_flags,
        resolved_this_release,
        report_date
    )
    logger.info("Watch list report saved: %s", report_path)
    logger.info("Release changes report saved: %s", changes_report_path)

    send_change_notification(
        notification_message,
        data_changed,
        notifications_enabled
    )

    # checks canidates in the zip file downloaded
        #save_candidates(candidates)
        #no candidates yet
        #candidates = find_upcoming_purges(reservations, 30)

    # save_candidates(candidates)

    # print("\nReservations purging within 30 days:")

    #    for candidate in candidates:
    #        print("N-Number:", candidate["n_number"])
    #        print("Registrant:", candidate["registrant"])
    #        print("Type:", candidate["reservation_type"])
    #        print("Category:", candidate["category"])
    #        print("Purge Date:", candidate["purge_date"])
    #        print("Days Until Purge:", candidate["days_until_purge"])
    #        print("----------------")

    # print("Total candidates:", len(candidates))
    # print("candidate snapshots stored:", count_snapshots())
        #checks the sql if duplicates exisit
    # print("Duplicate snapshot groups:", count_duplicate_snapshots)

            #tests the details loopup on the first removed n_number
            #if removed_reservations:
            #   first_removed = removed_reservations[0]
            #  details = get_reservation_details(
            #     first_removed, 
                #    previous_date
                #   )
                #print("\nTest removed reservations:")
                #print(details)

    logger.info("N-number Monitor completed successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FAA N-Number Monitor"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show monitor status without running an FAA check"
    )

    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Run the monitor without sending Discord notifications"
        )



    args = parser.parse_args()

    try:
        if args.status:
            show_status()
        else:
            main(
                notifications_enabled=not args.no_notify
            )

    except Exception as e:
        logger.exception("N-number Monitor crashed")

        failure_message = build_failure_notification(e)

        try:
            send_discord_notification(failure_message)
        except Exception:
            logger.exception(
                "Failed to send Discord failure notification"
            )

        raise