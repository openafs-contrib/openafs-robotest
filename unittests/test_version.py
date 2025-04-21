import re
import OpenAFSLibrary


def test_version():
    assert hasattr(OpenAFSLibrary, "__version__")
    assert re.match(r"\d+\.\d+\.\d+", OpenAFSLibrary.__version__)
