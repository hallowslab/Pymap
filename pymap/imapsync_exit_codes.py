"""imapsync process exit codes (see imapsync source EXIT_* constants)."""

IMAPSYNC_EXIT_CODES: dict[int, str] = {
    0: "OK",
    1: "CATCH_ALL",
    6: "EXIT_SIGNALLED",
    7: "EXIT_BY_FILE",
    8: "EXIT_PID_FILE_ERROR",
    10: "EXIT_CONNECTION_FAILURE",
    12: "EXIT_TLS_FAILURE",
    16: "EXIT_AUTHENTICATION_FAILURE",
    21: "EXIT_SUBFOLDER1_NO_EXISTS",
    64: "BAD_USAGE",
    66: "NO_INPUT",
    69: "SERVICE_UNAVAILABLE",
    70: "INTERNAL_SOFTWARE_ERROR",
    101: "EXIT_CONNECTION_FAILURE_HOST1",
    102: "EXIT_CONNECTION_FAILURE_HOST2",
    111: "EXIT_WITH_ERRORS",
    112: "EXIT_WITH_ERRORS_MAX",
    113: "EXIT_OVERQUOTA",
    114: "EXIT_ERR_APPEND",
    115: "EXIT_ERR_FETCH",
    116: "EXIT_ERR_CREATE",
    117: "EXIT_ERR_SELECT",
    118: "EXIT_TRANSFER_EXCEEDED",
    119: "EXIT_ERR_APPEND_VIRUS",
    161: "EXIT_AUTHENTICATION_FAILURE_USER1",
    162: "EXIT_AUTHENTICATION_FAILURE_USER2",
    254: "EXIT_TESTS_FAILED",
}


def describe_exit_code(code: int | None) -> str:
    if code is None:
        return ""
    label = IMAPSYNC_EXIT_CODES.get(code)
    if label:
        return label
    return f"UNKNOWN_EXIT_CODE ({code})"
