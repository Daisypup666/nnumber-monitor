import io
import zipfile
import pytest
import requests
import app.faa_downloader as faa_downloader
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


def test_faa_download_retries_then_succeeds(
    tmp_path,
    monkeypatch
):
    attempts = {"count": 0}

    # Build a fake but valid FAA ZIP in memory.
    fake_zip = io.BytesIO()

    with zipfile.ZipFile(fake_zip, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "TEST RESERVED DATA"
        )
        archive.writestr(
            "MASTER.txt",
            "TEST MASTER DATA"
        )

    fake_zip_bytes = fake_zip.getvalue()

    class FakeResponse:
        status_code = 200
        content = fake_zip_bytes

        def raise_for_status(self):
            pass

    def fake_get(*args, **kwargs):
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise requests.ConnectionError(
                "Temporary FAA connection failure"
            )

        return FakeResponse()

    # Replace the real network request.
    monkeypatch.setattr(
        faa_downloader.requests,
        "get",
        fake_get
    )

    # Don't actually wait 5 seconds during the test.
    monkeypatch.setattr(
        faa_downloader.time,
        "sleep",
        lambda seconds: None
    )

    # Keep test archives isolated from real FAA data.
    monkeypatch.setattr(
        faa_downloader,
        "FAA_ARCHIVE_DIR",
        tmp_path
    )

    zip_path, data_changed = (
        faa_downloader.check_faa_connection()
    )

    assert attempts["count"] == 3
    assert zip_path.exists()
    assert data_changed is True

def test_faa_download_raises_after_all_retries(
    monkeypatch
):
    attempts = {"count": 0}

    def fake_get(*args, **kwargs):
        attempts["count"] += 1

        raise requests.ConnectionError(
            "FAA server unavailable"
        )

    monkeypatch.setattr(
        faa_downloader.requests,
        "get",
        fake_get
    )

    # Prevent the test from actually waiting 5 seconds
    monkeypatch.setattr(
        faa_downloader.time,
        "sleep",
        lambda seconds: None
    )

    with pytest.raises(
        requests.ConnectionError,
        match="FAA server unavailable"
    ):
        faa_downloader.check_faa_connection()

    assert attempts["count"] == 3

def test_faa_zip_missing_master_is_rejected(
    tmp_path,
    monkeypatch
):
    # Build a fake FAA ZIP missing the MASTER.txt file.
    fake_zip = io.BytesIO()

    with zipfile.ZipFile(fake_zip, "w") as archive:
        archive.writestr(
            "RESERVED.txt",
            "TEST RESERVED DATA"
        )
        # Intentionally omitting MASTER.txt

    fake_zip_bytes = fake_zip.getvalue()

    class FakeResponse:
        status_code = 200
        content = fake_zip_bytes

        def raise_for_status(self):
            pass

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        faa_downloader.requests,
        "get",
        fake_get
    )

    with pytest.raises(
        ValueError,
        match="Downloaded FAA ZIP is missing required files: MASTER.txt"
    ):
        faa_downloader.check_faa_connection()

def test_faa_zip_missing_reserved_is_rejected(
    tmp_path,
    monkeypatch
):
    fake_zip = io.BytesIO()

    # Valid ZIP, but intentionally missing RESERVED.txt
    with zipfile.ZipFile(fake_zip, "w") as archive:
        archive.writestr(
            "MASTER.txt",
            "TEST MASTER DATA"
        )

    fake_zip_bytes = fake_zip.getvalue()

    class FakeResponse:
        status_code = 200
        content = fake_zip_bytes

        def raise_for_status(self):
            pass

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        faa_downloader.requests,
        "get",
        fake_get
    )

    monkeypatch.setattr(
        faa_downloader,
        "FAA_ARCHIVE_DIR",
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="RESERVED.txt"
    ):
        faa_downloader.check_faa_connection()

