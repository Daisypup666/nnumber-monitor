import zipfile

from app.faa_downloader import calculate_zip_member_hash


def test_zip_member_hash_matches_identical_content(tmp_path):
    zip_one = tmp_path / "one.zip"
    zip_two = tmp_path / "two.zip"

    # Create two different ZIP files containing
    # identical FAA reservation data.
    with zipfile.ZipFile(zip_one, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "N12345,TEST OWNER,TEST DATA"
        )

    with zipfile.ZipFile(zip_two, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "N12345,TEST OWNER,TEST DATA"
        )

    hash_one = calculate_zip_member_hash(
        zip_one,
        "RESERVED.txt"
    )

    hash_two = calculate_zip_member_hash(
        zip_two,
        "RESERVED.txt"
    )

    assert hash_one == hash_two

def test_zip_member_hash_detects_changed_content(tmp_path):
    zip_one = tmp_path / "one.zip"
    zip_two = tmp_path / "two.zip"

    with zipfile.ZipFile(zip_one, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "N12345,TEST OWNER,ORIGINAL DATA"
        )

    with zipfile.ZipFile(zip_two, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "N12345,TEST OWNER,CHANGED DATA"
        )

    hash_one = calculate_zip_member_hash(
        zip_one,
        "RESERVED.txt"
    )

    hash_two = calculate_zip_member_hash(
        zip_two,
        "RESERVED.txt"
    )

    assert hash_one != hash_two
    