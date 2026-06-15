def test_version() -> None:
    from marketiq import __version__

    assert __version__ == "0.1.0"
