from pathlib import Path
import sqlite3
from datetime import date

#-----------------------------------------------
# DATABASE LOCATION
#-----------------------------------------------

DATA_DIR = Path("data")
DATABASE_PATH = DATA_DIR / "nnumber_monitor.db"

#-----------------------------------------------
#CREAE/ INITALIZE DATABASE
#-----------------------------------------------

def initialize_database():
    #Create the data folder if it does not already exist.
    DATA_DIR.mkdir(exist_ok=True)

    #Open the SQlite database
    #If the database file does not exist, SQlite creates it
    connection = sqlite3.connect(DATABASE_PATH)

#TEMPORTARY - remove the incorrectly created table
    #connection.execute("""
    #    DROP TABLE IF EXISTS faa_reservation_snapshots
    #""")
#recreate it with the correct columns
    connection.execute("""
        CREATE TABLE IF NOT EXISTS reservation_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
             n_number TEXT NOT NULL,
            registrant TEXT,
            reservation_type TEXT,
            category TEXT,
            purge_date TEXT,
            observed_date TEXT NOT NULL
        )  
    """)

    #prevent the same N-number from being saved
    #more thann once on the same day. 
    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_n_number_observed_date
        ON reservation_snapshots (n_number, Observed_date)   
""")

    # NEW flagged N-number table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS flagged_n_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            n_number TEXT NOT NULL,
            registrant TEXT,
            reservation_type TEXT,
            category TEXT,
            purge_date TEXT,
            last_observed TEXT NOT NULL,
            detected_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'FLAGGED',
            resolved_date TEXT,
            UNIQUE(n_number, detected_date)
        )
    """) 
#-----------------------------------------------------
#FULL FAA RESERVATION SNAPSHOT
#-----------------------------------------------------
    connection.execute("""
        CREATE TABLE IF NOT EXISTS faa_reservation_snapshots ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            n_number TEXT NOT NULL,
            registrant TEXT,
            reservation_type TEXT,
            category TEXT,
            purge_date TEXT,
            observed_date TEXT NOT NULL    
         )
    """)

    #give the full FAA table the same duplicate protection
    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_faa_snapshot_n_number_date
        ON faa_reservation_snapshots (n_number, observed_date)
         
    """)

    #CREATE TABLE changes the database, so save the change
    connection.commit()
    #We are finsihed with this connection. 
    connection.close()

#-----------------------------------------------
#SAVE FAA CANDIDATES
#-----------------------------------------------

def save_candidates(candidates):
    connection = sqlite3.connect(DATABASE_PATH)

    observed_date = date.today().isoformat()

    for candidate in candidates:
        connection.execute("""
            INSERT OR IGNORE INTO reservation_snapshots (
                n_number,
             registrant,
                reservation_type,
                category,
                purge_date,
                observed_date
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,(
            candidate["n_number"],
            candidate["registrant"],
            candidate["reservation_type"],
            candidate["category"],
            candidate["purge_date"].isoformat(),
            observed_date,
        ))

def save_reservations(reservations, observed_date):
    connection = sqlite3.connect(DATABASE_PATH)

    for reservation in reservations:
        purge_date = reservation["purge_date"]
    #    observed_date = date.today().isoformat()
        #some FAA reservations do not have a purge date.
        #only convert it to text if a date actually exists
        if purge_date is not None:
            purge_date = purge_date.isoformat()

        connection.execute("""
            INSERT OR IGNORE INTO faa_reservation_snapshots ( 
                n_number,
                registrant,
                reservation_type,
                category,
                purge_date,
                observed_date
            )
            VALUES (?, ?, ?, ?, ?, ? )
        """, (
            reservation["n_number"],
            reservation["registrant"],
            reservation["reservation_type"],
            reservation["category"],
            purge_date,
            observed_date,
        ))
    connection.commit()
    connection.close()


def count_reservation_snapshots():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT COUNT(*)
        FROM faa_reservation_snapshots
    """)

    count = cursor.fetchone()[0]

    connection.close()

    return count
#-----------------------------------------------
#count saved snapshots
#-----------------------------------------------

def count_snapshots():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT COUNT(*)
        FROM reservation_snapshots
""")

    #fetchone() returns row.
    #
    # For example:
    #
    #(1468,)
    #
    # [0] extracts the number from the tuple.
    count = cursor.fetchone()[0]

    #SELECT does not change the database, 
    #so we do NOT connection.comit().
    connection.close()

    #send the count back to main.py
    return count

def count_duplicate_snapshots():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT n_number, observed_date
            FROM reservation_snapshots
            GROUP BY n_number, observed_date
            HAVING COUNT(*) > 1
        )
""")

    count = cursor.fetchone()[0]

    connection.close()

    return count

def get_snapshot_dates():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT DISTINCT observed_date
        FROM faa_reservation_snapshots
        ORDER BY observed_date DESC
""")

    rows = cursor.fetchall()

    connection.close()

    return [row[0] for row in rows]

def get_removed_reservations(current_date, previous_date):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.execute("""
        SELECT n_number
        FROM faa_reservation_snapshots
        WHERE observed_date = ?
    
        EXCEPT

        SELECT n_number
        FROM faa_reservation_snapshots
        WHERE observed_date = ? 
    """, (previous_date, current_date))

    rows = cursor.fetchall()
    connection.close()
    return [row[0] for row in rows]

def get_reservation_details(n_number, observed_date):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.execute("""
        SELECT 
            n_number,
            registrant,
            reservation_type,
            category,
            purge_date,
            observed_date
        FROM faa_reservation_snapshots
        WHERE n_number = ? 
        AND observed_date = ?
    """, (n_number, observed_date))
    row = cursor.fetchone()
    connection.close()
    return row

def save_flagged_n_number(
    n_number,
    registrant,
    reservation_type,
    category,
    purge_date,
    last_observed,
    detected_date
):
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        INSERT OR IGNORE INTO flagged_n_numbers (
            n_number,
            registrant,
            reservation_type,
            category,
            purge_date,
            last_observed,
            detected_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'FLAGGED')
    """, (
        n_number,
        registrant,
        reservation_type,
        category,
        purge_date,
        last_observed,
        detected_date
    ))

    connection.commit()
    connection.close()

def get_flagged_n_numbers():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT
            n_number,
            registrant,
            reservation_type,
            category,
            purge_date,
            last_observed,
            detected_date,
            status
        FROM flagged_n_numbers
        WHERE status = 'FLAGGED'
        ORDER BY detected_date ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows

def update_flag_status(n_number, status, resolved_date):
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        UPDATE flagged_n_numbers
        SET status = ?,
            resolved_date = ?
        WHERE n_number = ?
        AND status = 'FLAGGED'
    """, (status, resolved_date, n_number))

    connection.commit()
    connection.close()

def get_flag_summary():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT status, COUNT(*)
        FROM flagged_n_numbers
        GROUP BY status
    """)

    rows = cursor.fetchall()
    connection.close()

    return dict(rows)

def get_resolved_flags():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute("""
        SELECT
            n_number,
            registrant,
            reservation_type,
            category,
            purge_date,
            last_observed,
            detected_date,
            status,
            resolved_date
        FROM flagged_n_numbers
        WHERE status != 'FLAGGED'
        ORDER BY resolved_date DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows
    