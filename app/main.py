from database import (
    get_removed_reservations,
    initialize_database,
    save_candidates,
    count_snapshots,
    # imports duplicate snapshot
    #count_duplicate_snapshots,
    save_reservations,
    count_reservation_snapshots,
    get_snapshot_dates,
    get_removed_reservations,
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
)




def main():
    print("N-number Monitor")
    print("Starting application...")
    faa_zip_path, data_changed = check_faa_connection()
    initialize_database()

    #show_data_directory()

    #print("\nFiles inside FAA database:")
    #list_zip_contents()
    #print("\nFirst 5 rows fo RESERVED.txt:")
    #preview_reserved_data()
    #print("\nParsed reservations: ")
    #parse_reserved_data()
    #29 -36 commented out as debug/exploation output

   # print("\nReservations purging within 30 days:") 
   #no filter in place atm
    reservations = load_reservations(faa_zip_path)
    print("Total FAA reservation records:", len(reservations))
   
   #old method:
   # snapshot_date = date.today().isoformat()
    snapshot_date = get_snapshot_date_from_path(faa_zip_path)
  
    if data_changed:
        save_reservations(reservations, snapshot_date)
        print("New FAA snapshot saved. ")
    else:
        print("Data has not changed since the last snapshot.")
   
    save_reservations(reservations, snapshot_date)

    print(
        "FAA reservation snapshots stored:",
        count_reservation_snapshots() 
    )
    #save_candidates(candidates)
    #no candidates yet
    candidates = find_upcoming_purges(reservations, 30)

    save_candidates(candidates)

    print("\nReservations purging within 30 days:")

#    for candidate in candidates:
#        print("N-Number:", candidate["n_number"])
#        print("Registrant:", candidate["registrant"])
#        print("Type:", candidate["reservation_type"])
#        print("Category:", candidate["category"])
#        print("Purge Date:", candidate["purge_date"])
#        print("Days Until Purge:", candidate["days_until_purge"])
#        print("----------------")

    print("Total candidates:", len(candidates))
    print("candidate snapshots stored:", count_snapshots())
    #checks the sql if duplicates exisit
   # print("Duplicate snapshot groups:", count_duplicate_snapshots)

    snapshot_dates = get_snapshot_dates()
    print("Snapshot dates:", snapshot_dates)

    if len(snapshot_dates) < 2:
        print("waiting for another FAA snapshot before comparing changes.")

    else:
        current_date = snapshot_dates[0]
        previous_date = snapshot_dates[1]

        removed_reservations = get_removed_reservations(

        )


if __name__ == "__main__":
    main()
