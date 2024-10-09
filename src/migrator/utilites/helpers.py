import logging
import subprocess
import re
from os.path import join, abspath
import shlex

from typing import Dict, List, Optional

from migrator.utilites.strings import (
    DATE_REGEX,
    SPAM_ERROR,
    IMAPSYNC_CODES,
)

logger = logging.getLogger(__name__)


def match_status(code: str) -> str:
    if code in IMAPSYNC_CODES.keys():
        return IMAPSYNC_CODES[code]
    return code


def grep_errors(log_directory: str, log_path: str, timeout: int = 5) -> str:
    try:
        content = subprocess.check_output(
            ["grep", "Err", join(log_directory, log_path)],
            timeout=timeout,
            text=True,
        )
        return content
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # return f"Failed to grep contents from file {join(log_directory, log_path)}"
        return ""


def check_failed_is_only_spam(content: str) -> bool:
    lines: List[str] = [x for x in content.split("\n") if len(x) > 1]
    for line in lines:
        if re.match(SPAM_ERROR, line):
            return True
    return False


def sub_check_output(command: str, filename: str, timeout: int = 5) -> str:
    f_path = abspath(filename)
    logger.debug("Command is: %s", command)
    logger.debug("SHLEX interpreted as: %s", shlex.split(f"{command} {f_path}"))
    try:
        return subprocess.check_output(
            shlex.split(f"{command} {f_path}"),
            timeout=timeout,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Failed to run command: {command}:{e}"
    except subprocess.TimeoutExpired:
        return "Timeout expired"
    except Exception as e:
        logger.critical("Unhandled exception: %s", str(e), exc_info=True)
        raise e


def get_status(full_path: str, timeout: int) -> str:
    has_status: str = sub_check_output(
        "grep -E 'Exiting with return value *'",
        full_path,
        timeout=timeout,
    )
    status = "Running" if len(has_status) == 0 else has_status.split(" ")[4]
    status_message: str = match_status(status)
    if status != "0" and "Failed" in status_message:
        is_spam = check_failed_is_only_spam(status)
        logger.debug("Has spam failed?: %s", is_spam)
        status_message = "Transfer ok, spam not synced" if is_spam else status_message
    return status_message


def get_start_time(full_path: str, timeout: int) -> str:
    # start_time = time.strptime(start_time, "%A  %B %Y-%m-%d")
    start_time: str = sub_check_output(
        "grep -E 'Transfer started at *'",
        full_path,
        timeout=timeout,
    )
    start_time_match: Optional[re.Match[str]] = re.match(DATE_REGEX, start_time)
    if start_time_match:
        start_time = start_time_match.group("time")
    else:
        start_time = "Failed to parse"
    return start_time


def get_end_time(full_path: str, timeout: int) -> str:
    end_time: str = sub_check_output(
        "grep -E 'Transfer ended on *'",
        full_path,
        timeout=timeout,
    )
    end_time_match: Optional[re.Match[str]] = re.match(DATE_REGEX, end_time)
    if end_time_match:
        end_time = end_time_match.group("time")
    else:
        end_time = "Check status ->"
    return end_time


def get_logs_status(
    log_directory: str, log_path: str, timeout: int = 5
) -> Dict[str, str]:
    # FIXME: This might have some issues on directories with a large amount of files
    # TODO: Maybe stop using so many regular expressions and just use grep awk and whatever.....
    full_path = join(log_directory, log_path)
    status_message = get_status(full_path, timeout)
    start_time = get_start_time(full_path, timeout)
    end_time = get_end_time(full_path, timeout)
    return {
        "log_file": log_path,
        "start_time": start_time,
        "end_time": end_time,
        "status": status_message,
    }


# def validate_imap_credentials(host, port, username, password):
#     try:
#         # Connect to the server
#         mail = imaplib.IMAP4(host, port)

#         # Attempt to login
#         mail.login(username, password)

#         print("Login successful!")

#         # Logout
#         mail.logout()

#         return True
#     except imaplib.IMAP4.error as e:
#         print(f"Login failed: {e}")
#         return False
