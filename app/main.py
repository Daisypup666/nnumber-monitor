from database import (
    get_removed_reservations,
    initialize_database,
    #save_candidates,
    count_snapshots,
    # imports duplicate snapshot
    #count_duplicate_snapshots,
    save_reservations,
    count_reservation_snapshots,
    get_snapshot_dates,
    get_removed_reservations,
    get_reservation_details,
)
from faa_downloader import (
    #show_data_directory,
    #list_zip_contents,
    #preview_reserved_data,
    #parse_reserved_data,
    #commented out as they are no longer
    #used only used for exploration of the zip file
    find_upcoming_purges,
    get_snapshot_date_from_path,
    load_reservations,
    check_faa_connection,
    preview_master_data,
    load_registered_n_numbers,
)
from pathlib import Path

def import_archived_snapshot(zip_path):
    reservations = load_reservations(zip_path)
    snapshot_date = get_snapshot_date_from_path(zip_path)

    #print("Importing archived snapshot:", snapshot_date)
    #print("Reservation records:", len(reservations))

    save_reservations(reservations, snapshot_date)

    #print("Archived snapshot imported.")


def main():
    print("N-number Monitor")
    print("Starting application...")
    faa_zip_path, data_changed = check_faa_connection()
    initialize_database()
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
   #no filter in place atm
    reservations = load_reservations(faa_zip_path)
    print("Total FAA reservation records:", len(reservations))

    registered_n_numbers = load_registered_n_numbers(faa_zip_path)
    print(
        "Registered aircraft N-numbers loaded:",
        len(registered_n_numbers)
    )
    print("Total FAA reservation records:", len(reservations))

   #old method:
   # snapshot_date = date.today().isoformat()
    snapshot_date = get_snapshot_date_from_path(faa_zip_path)

    #print("Snapshot date being saved:", snapshot_date)

  
    if data_changed:
        save_reservations(reservations, snapshot_date)
        print("New FAA snapshot saved. ")
    else:
        print("Data has not changed since the last snapshot.")
   
  
    print(
        "FAA reservation snapshots stored:",
        count_reservation_snapshots() 
    )

   

    snapshot_dates = get_snapshot_dates()
    print("Snapshot dates:", snapshot_dates)

    if len(snapshot_dates) < 2:
        print("waiting for another FAA snapshot before comparing changes.")

    else:
        current_date = snapshot_dates[0]
        previous_date = snapshot_dates[1]

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
        print("\n--- Comparison Sumarry --")
        print("Removed reservations:", len(removed_reservations))
        print("Registered aircraft:", registered_count)
        print("Flagged for review:", flagged_count)

    # checks canidates in the zip file downloaded
        #save_candidates(candidates)
        #no candidates yet
        candidates = find_upcoming_purges(reservations, 30)

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

if __name__ == "__main__":
    main()
