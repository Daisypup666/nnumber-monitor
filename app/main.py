from database import (
    initialize_database,
    save_candidates,
    count_snapshots,
    # imports duplicate snapshot
    #count_duplicate_snapshots,
    save_reservations,
    count_reservation_snapshots,
    get_snapshot_dates
)
from faa_downloader import (
    #show_data_directory,
    #list_zip_contents,
    #preview_reserved_data,
    #parse_reserved_data,
    #commented out as they are no longer
    #used only used for exploration of the zip file
    find_upcoming_purges,
    load_reservations,
    check_faa_connection,
)



def main():
    print("N-number Monitor")
    print("Starting application...")
    faa_zip_path = check_faa_connection()
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

    save_reservations(reservations)

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

    #else:
        #comapre newest two snapshots


if __name__ == "__main__":
    main()
