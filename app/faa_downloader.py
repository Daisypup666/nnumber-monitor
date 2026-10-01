from pathlib import Path
import zipfile
import csv
import io
from datetime import datetime, date
import requests
import hashlib
import time


DATA_DIR = Path("data")
FAA_URL = "https://registry.faa.gov/database/ReleasableAircraft.zip"
FAA_ARCHIVE_DIR = DATA_DIR / "faa_archive"

def show_data_directory():
    print(f"FAA data will be stored in: {DATA_DIR.resolve()}")
    FAA_ZIP_PATH = DATA_DIR / "ReleasableAircraft.zip"
#    TEMP_ZIP_PATH = DATA_DIR / "ReleasableAircraft.zip"

def get_snapshot_date_from_path(zip_path):
    filename = zip_path.stem
    date_text = filename.split("_")[-1]
    return date_text

def check_faa_connection():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                FAA_URL,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            print(
                f"FAA response status: {response.status_code}"
            )

            break

        except requests.RequestException as error:
            print(
                f"FAA download attempt "
                f"{attempt}/{max_attempts} failed: {error}"
            )

            if attempt == max_attempts:
                raise

            time.sleep(5)
    #print(f"Downloaded bytes: {len(response.content)}")

    FAA_ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    today = date.today().isoformat()

    zip_path = FAA_ARCHIVE_DIR / f"ReleasableAircraft_{today}.zip"

    with zipfile.ZipFile(io.BytesIO(response.content)) as faa_zip:
        file_names = faa_zip.namelist()

        required_files = {
           "RESERVED.txt",
           "MASTER.txt",
       }

        missing_files = required_files - set(file_names)
        if missing_files:
            raise ValueError(
                "Downloaded FAA ZIP is missing required files: "
                + ", ".join(sorted(missing_files))
            )
    #outside validation block
    with open(zip_path, "wb") as file:
        file.write(response.content)

    #print(f"FAA ZIP saved to: {zip_path}")

    #prints hash info
    previous_zip = get_previous_archive(zip_path)

    if previous_zip is None:
        print(
            "No previous FAA archive available for comparison."
        )
        data_changed = True

    else:
        current_reserved_hash = calculate_zip_member_hash(
            zip_path,
            "RESERVED.txt"
        )

        previous_reserved_hash = calculate_zip_member_hash(
            previous_zip,
            "RESERVED.txt"
        )

        current_master_hash = calculate_zip_member_hash(
            zip_path,
            "MASTER.txt"
        )

        previous_master_hash = calculate_zip_member_hash(
            previous_zip,
            "MASTER.txt"
        )

        reserved_changed = (
            current_reserved_hash != previous_reserved_hash
        )

        master_changed = (
            current_master_hash != previous_master_hash
        )

        data_changed = reserved_changed or master_changed

        if data_changed:
            print(
                "FAA data has changed since the last archive."
            )
        else:
            print(
                "FAA data has not changed since the last archive."
            )
            #starilizes archives
    cleanup_faa_archive(7)
    return zip_path, data_changed

#troubleshooting
#    with open(TEMP_ZIP_PATH, "wb") as file:
#       file.write(response.content)

#    print(f"Temporary ZIP saved to: {TEMP_ZIP_PATH}")
#cleaner fuct
def cleanup_faa_archive(keep=7):
    zip_files = sorted(
        FAA_ARCHIVE_DIR.glob("ReleasableAircraft_*.zip"),
        reverse=True
    )

    old_files = zip_files[keep:]

    for old_file in old_files:
        old_file.unlink()
        print(f"Deleted old FAA archive: {old_file}")

def list_zip_contents():
    zip_path = DATA_DIR / "ReleasableAircraft.zip"

    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        for file_name in faa_zip.namelist():
            print(file_name)

def preview_reserved_data():
    zip_path = DATA_DIR / "ReleasableAircraft.zip"

    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        with faa_zip.open("RESERVED.txt") as reserved_file:
            for _ in range(5):
                line = reserved_file.readline()
                print(line.decode("utf-8").strip())

def preview_master_data(zip_path):
    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        with faa_zip.open("MASTER.txt") as master_file:
            text_file = io.TextIOWrapper(master_file)

            for _ in range(5):
                print(text_file.readline().strip())

def parse_faa_date(date_string):
    if not date_string:
        return None
    return datetime.strptime(date_string, "%Y%m%d").date()

def parse_reserved_data():
    zip_path = DATA_DIR / "releasableAircraft.zip"

    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        with faa_zip.open("RESERVED.txt") as reserved_files:

            text_file = io.TextIOWrapper(
                reserved_files,
                encoding="utf-8-sig"
            )

            reader = csv.DictReader(text_file)

            for _ in range(3):
                record = next(reader)

                purge_date = parse_faa_date(record["PURGE DATE"].strip())

                print("N-Number:", record["N-NUMBER"])
                print("Registrant:", record["REGISTRANT"])
                print("Purge Date:", purge_date)
                print("----------------")


def find_upcoming_purges(reservations, days_ahead=30):
    zip_path = DATA_DIR / "ReleasableAircraft.zip"
    today = date.today()
    candidates = []

    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        with faa_zip.open("RESERVED.txt") as reserved_file:
            text_file = io.TextIOWrapper(
                reserved_file,
                encoding="utf-8-sig"
            )

            reader = csv.DictReader(text_file)

            for record in reader:
                purge_date = parse_faa_date(
                    record["PURGE DATE"].strip()
                )

                reservation_type = record["TR"].strip()
                category = classify_reservation(reservation_type)

                if purge_date is None:
                    continue

                days_until_purge = (purge_date - today).days

                if 0 <= days_until_purge <= days_ahead:
                    candidate = {
                        "n_number": record["N-NUMBER"].strip(),
                        "registrant": record["REGISTRANT"].strip(),
                        "reservation_type": reservation_type,
                        "category": category,
                        "purge_date": purge_date,
                        "days_until_purge": days_until_purge,
                    }

                    candidates.append(candidate)

    return candidates

def classify_reservation(reservation_type):
    if reservation_type in ("A", "FN"):
        return "EXPIRING_RESERVATION"

    elif reservation_type == "FP":
        return "PAID_RESERVATION"

    elif reservation_type == "HD":
        return "CANCELED_HOLD"

    elif reservation_type in ("NC", "NN", "CN", "CE"):
        return "N_NUMBER_CHANGE"

    elif reservation_type in ("MF", "MT"):
        return "MANUFACTURER"

    elif reservation_type == "AA":
        return "NO_FEE_RESERVATION"

    else:
        return "UNKNOWN"

def load_reservations(zip_path):

     #   Old static ZIP loc; now loaded by zip_path ^
     #   zip_path = DATA_DIR / "ReleasableAircraft.zip"

        reservations = []

        with zipfile.ZipFile(zip_path, "r") as faa_zip:
            with faa_zip.open("RESERVED.txt") as reserved_file:
                text_file = io.TextIOWrapper(
                    reserved_file,
                    encoding="utf-8-sig"
                )

                reader = csv.DictReader(text_file)

                for record in reader:
                    purge_date = parse_faa_date(
                        record["PURGE DATE"].strip()
                    )

                    reservation_type = record["TR"].strip()
                    category = classify_reservation(reservation_type)

                    reservation = {
                        "n_number": record["N-NUMBER"].strip(),
                        "registrant": record["REGISTRANT"].strip(),
                        "reservation_type": reservation_type,
                        "category": category,
                        "purge_date": purge_date,
                    }

                    reservations.append(reservation)
        return reservations

def load_registered_n_numbers(zip_path):
    registered_n_numbers = set()

    with zipfile.ZipFile(zip_path, "r") as faa_zip:
        text_file = io.TextIOWrapper(
            faa_zip.open("MASTER.txt"),
            encoding="utf-8-sig"
        )

        reader = csv.DictReader(text_file)

        for row in reader:
            n_number = row["N-NUMBER"].strip()

            if n_number:
                registered_n_numbers.add(n_number)
    return registered_n_numbers

def calculate_file_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()

def get_previous_archive(current_zip_path):
    current_zip_path = Path(current_zip_path)

    current_date = get_snapshot_date_from_path(current_zip_path)

    zip_files = sorted(
        FAA_ARCHIVE_DIR.glob("*.zip"),
        reverse=True
    )

    for zip_file in zip_files:
        archive_date = get_snapshot_date_from_path(zip_file)

        if archive_date < current_date:
            return zip_file

    return None

def calculate_zip_member_hash(zip_path, member_name):
    sha256 = hashlib.sha256()

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        with zip_file.open(member_name) as file:
            while True:
                chunk = file.read(8192)

                if not chunk:
                    break

                sha256.update(chunk)

    return sha256.hexdigest()