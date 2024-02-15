from typing import List
import pytest
from core.pymap_core import ScriptGenerator

# Just here for the dev log level

from tests import (
    RANDOM_VALID_CREDS_3,
    RANDOM_VALID_CREDS_4,
)


@pytest.mark.parametrize(
    "test_input",
    [
        # These should all return None
        (""),
        ("n1x28ex31xe2"),
        ("random.email@gmail.com"),
        ("This gets parsed by the second method, unfortunately returns bad content"),
    ],
)
def test_api_discards_invalid_inputs(test_input: List[str]) -> None:
    x = ScriptGenerator("127.0.0.1", "127.0.0.1", domain="test.com")
    scripts = x.process_strings(test_input)
    assert isinstance(scripts, list)
    assert len(scripts) == 0


# USER PASSWORD
@pytest.mark.parametrize("test_input", RANDOM_VALID_CREDS_3)
def test_returns_parsed_line_1_user(test_input: List[str]) -> None:
    x = ScriptGenerator("127.0.0.1", "127.0.0.2", domain="test.com")
    scripts = x.process_strings(test_input)
    for line in scripts:
        parts = line.split()
        host1 = parts[parts.index("--host1") + 1]
        host2 = parts[parts.index("--host2") + 1]
        user1 = parts[parts.index("--user1") + 1]
        user2 = parts[parts.index("--user2") + 1]
        password1 = parts[parts.index("--password1") + 1].strip("'")
        password2 = parts[parts.index("--password2") + 1].strip("'")
        assert host1 == "127.0.0.1"
        assert host2 == "127.0.0.2"
        assert user1 in line
        assert user2 in line
        assert password1 in line
        assert password2 in line


# USER1 PASSWORD1 USER2 PASSWORD2""
@pytest.mark.parametrize("test_input", RANDOM_VALID_CREDS_4)
def test_returns_parsed_line_2_users(test_input: List[str]) -> None:
    x = ScriptGenerator("127.0.0.1", "127.0.0.1", domain="test.com")
    scripts = x.process_strings(test_input)
    for line in scripts:
        parts = line.split()
        host1 = parts[parts.index("--host1") + 1]
        host2 = parts[parts.index("--host2") + 1]
        user1 = parts[parts.index("--user1") + 1]
        user2 = parts[parts.index("--user2") + 1]
        password1 = parts[parts.index("--password1") + 1].strip("'")
        password2 = parts[parts.index("--password2") + 1].strip("'")
        assert host1 == "127.0.0.1"
        assert host2 == "127.0.0.1"
        assert user1 in line
        assert user2 in line
        assert password1 in line
        assert password2 in line
