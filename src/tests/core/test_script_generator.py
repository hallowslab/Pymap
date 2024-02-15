from typing import Dict, Union
import pytest
from unittest.mock import patch, mock_open, call
from core.pymap_core import ScriptGenerator

config_type = Dict[str, Union[list[list[str]], str]]


@pytest.fixture
def mock_config() -> config_type:
    return {"LOGDIR": "/var/log/test", "HOSTS": [["sv[0-9]+", ".example.com"]]}


@pytest.fixture
def mock_generator(mock_config: config_type) -> ScriptGenerator:
    generator = ScriptGenerator("sv00", "host2")
    generator.config = mock_config
    return generator


def test_process_file_single_line(
    mock_generator: ScriptGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mocking isfile and open functions
    monkeypatch.setattr("os.path.isfile", lambda x: True)
    with patch(
        "builtins.open",
        mock_open(read_data="user1@domain1.com pass1 user2@domain2.com pass2\n"),
    ) as m:
        # Calling the method
        mock_generator.process_file("test_file.txt")

    expected_output_calls = [
        call(
            [
                mock_generator.FORMAT_STRING.format(
                    mock_generator.host1,
                    "user1@domain1.com",
                    "pass1",
                    mock_generator.host2,
                    "user2@domain2.com",
                    "pass2",
                    f"{mock_generator.host1}__{mock_generator.host2}__user1@domain1.com--user2@domain2.com.log",
                )
                + "\n"
            ]
        )
    ]
    assert m().writelines.call_args_list == expected_output_calls
    # Add additional assertions based on your expected behavior


def test_process_file_multiple_lines(
    mock_generator: ScriptGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Mocking isfile and open functions
    monkeypatch.setattr("os.path.isfile", lambda x: True)
    m = mock_open(
        read_data="user1@domain1.com pass1\nuser2@domain2.com pass2\nuser3@domain3.com pass3\nuser4@domain4.com pass4\n"
    )
    with patch("builtins.open", m):
        # Calling the method
        mock_generator.process_file("test_file.txt")
    # Assertions
    assert m.call_count == 2  # Ensure open is called twice, 2 lines read
    assert (
        m.call_args_list[0][0][0] == "test_file.txt"
    )  # Ensure open is called with the correct file path

    # Assuming line_count is 2 for simplicity
    expected_output_calls = [
        call(
            [
                mock_generator.FORMAT_STRING.format(
                    mock_generator.host1,
                    "user1@domain1.com",
                    "pass1",
                    mock_generator.host2,
                    "user1@domain1.com",
                    "pass1",
                    f"{mock_generator.host1}__{mock_generator.host2}__user1@domain1.com--user1@domain1.com.log",
                )
                + "\n",
                mock_generator.FORMAT_STRING.format(
                    mock_generator.host1,
                    "user2@domain2.com",
                    "pass2",
                    mock_generator.host2,
                    "user2@domain2.com",
                    "pass2",
                    f"{mock_generator.host1}__{mock_generator.host2}__user2@domain2.com--user2@domain2.com.log",
                )
                + "\n",
                mock_generator.FORMAT_STRING.format(
                    mock_generator.host1,
                    "user3@domain3.com",
                    "pass3",
                    mock_generator.host2,
                    "user3@domain3.com",
                    "pass3",
                    f"{mock_generator.host1}__{mock_generator.host2}__user3@domain3.com--user3@domain3.com.log",
                )
                + "\n",
                mock_generator.FORMAT_STRING.format(
                    mock_generator.host1,
                    "user4@domain4.com",
                    "pass4",
                    mock_generator.host2,
                    "user4@domain4.com",
                    "pass4",
                    f"{mock_generator.host1}__{mock_generator.host2}__user4@domain4.com--user4@domain4.com.log",
                )
                + "\n",
            ]
        )
    ]
    assert m().writelines.call_args_list == expected_output_calls
    # Add additional assertions based on your expected behavior


def test_process_strings(mock_generator: ScriptGenerator) -> None:
    strings = ["user1@example.com pass1 user2@domain.com pass2", "\n"]
    scripts = mock_generator.process_strings(strings)
    expected_output_calls = [
        mock_generator.FORMAT_STRING.format(
            mock_generator.host1,
            "user1@example.com",
            "pass1",
            mock_generator.host2,
            "user2@domain.com",
            "pass2",
            f"{mock_generator.host1}__{mock_generator.host2}__user1@example.com--user2@domain.com.log",
        )
    ]
    assert scripts == expected_output_calls
    # Add assertions here to check if the generated scripts match the expected output


def test_write_output(
    mock_generator: ScriptGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_open_func = mock_open()
    monkeypatch.setattr("builtins.open", mock_open_func)

    mock_generator.write_output(["script1", "script2"])

    # Ensure the correct file is opened for writing
    mock_open_func.assert_called_once_with("sync_0.sh", "w")

    # Ensure the correct lines are written to the file
    expected_lines = ["script1\n", "script2\n"]
    mock_open_func().writelines.assert_called_once_with(expected_lines)


def test_verify_matches_hosts(mock_generator: ScriptGenerator) -> None:
    mock_generator.config["HOSTS"] = [
        ["^sv[0-9]{2}$", ".example.com"],
        ["^VPS[0-9]{0,1}$", ".example.dev"],
    ]
    result1 = mock_generator.verify_host("sv00")
    result2 = mock_generator.verify_host("VPS1")
    result3 = mock_generator.verify_host("ABC123")
    result4 = mock_generator.verify_host("VPS1000")
    assert result1 == "sv00.example.com"
    assert result2 == "VPS1.example.dev"
    assert result3 == "ABC123"
    assert result4 == "VPS1000"


def test_match_domain(mock_generator: ScriptGenerator) -> None:
    result = mock_generator.match_domain("user@example.com LR`T@9!dM4QJD$YhF6")
    assert result == "example.com"


def test_match_domain_fail(mock_generator: ScriptGenerator) -> None:
    r1 = mock_generator.match_domain("user@example LR`T@9!dM4QJD$YhF6")
    r2 = mock_generator.match_domain("user@example LR`T@example.rdfgha")
    assert r1 is None
    assert r2 is None
