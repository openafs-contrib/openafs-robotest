import pytest


@pytest.mark.order("first")
def test_import():
    from OpenAFSLibrary import OpenAFSLibrary

    assert hasattr(OpenAFSLibrary, "create_volume"), "create_volume keyword not found"
