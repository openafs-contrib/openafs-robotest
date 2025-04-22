from OpenAFSLibrary.keywords.dump import VolumeDump


def test_create_dump(tmp_path):
    filename = tmp_path / "test.dump"
    with VolumeDump(filename) as dump:
        dump.write(ord("v"), "L", 12345678)
    assert filename.exists()
