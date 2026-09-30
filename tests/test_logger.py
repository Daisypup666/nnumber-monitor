import app.logger as logger_module


def test_setup_logger_creates_log_file(tmp_path, monkeypatch):
    test_log = tmp_path / "nnumber_monitor.log"

    monkeypatch.setattr(
        logger_module,
        "LOG_DIR",
        tmp_path
    )

    monkeypatch.setattr(
        logger_module,
        "LOG_FILE",
        test_log
    )

    logger = logger_module.setup_logger()

    logger.info("Test log message")

    for handler in logger.handlers:
        handler.flush()

    assert test_log.exists()

    contents = test_log.read_text(encoding="utf-8")

    assert "INFO" in contents
    assert "Test log message" in contents