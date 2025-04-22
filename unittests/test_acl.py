import pytest
from OpenAFSLibrary.keywords.acl import normalize, AccessControlList


def test_normalize():
    assert normalize([]) == []
    assert normalize(["r"]) == ["r"]
    assert normalize(["a", "l", "r"]) == ["r", "l", "a"]
    assert normalize(["r", "r", "l"]) == ["r", "l"]
    assert normalize(list("adiklrw")) == list("rlidwka")
    assert normalize(list("kBCDGrAwEadFliH")) == list("rlidwkaABCDEFGH")
    with pytest.raises(AssertionError, match="Illegal rights character: b"):
        normalize(["a", "b", "c"])


def test_contains():
    a = AccessControlList.from_args(
        "system:administrators rlidwka",
        "system:anyuser rl",
        "user1 rl",
        "user2 rl",
        "user2 rwl",
        "user2 -l",
        "user3 +rlidwk",
        "user4 none",
    )
    assert a.contains("system:administrators", "rlidwka")
    assert a.contains("system:anyuser", "rl")
    assert a.contains("user1", "+rl")
    assert a.contains("user2", "rlw")
    assert a.contains("user2", "-l")
    assert a.contains("user3", "+rlidwk")
    assert not a.contains("user4", "")
    assert not a.contains("user1", "w")


def test_add():
    a = AccessControlList.from_args()
    b = AccessControlList.from_args("system:administrators rlidwka")
    a.add("system:administrators", "rlidwka")
    assert a == b

    a = AccessControlList.from_args("system:administrators rlidwka")
    b = AccessControlList.from_args(
        "system:administrators rlidwka", "system:anyuser rl"
    )
    a.add("system:anyuser", "rl")
    assert a == b

    a = AccessControlList.from_args("user1 wl")
    b = AccessControlList.from_args("user1 rwl")
    a.add("user1", "rl")
    assert a == b
