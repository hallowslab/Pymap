import logging
import json
import re
from argparse import Namespace, ArgumentParser
from typing import Any, List, Optional

logger = logging.getLogger("pymap_core.utils")


# Try to parse log level, default to 20/INFO
def set_logging(log_level: str) -> None:
    # On dry run DEBUG is always enabled
    numeric_level = getattr(logging, log_level.upper(), 20)
    logging.basicConfig(
        format="%(asctime)s - %(name)s >>> %(levelname)s: %(message)s",
        level=numeric_level,
        datefmt="%d/%m/%Y %I:%M:%S %p",
    )
    logging.info(
        "Logging instantiated with log level: %s",
        logging.getLevelName(logging.getLogger().level),
    )


def load_config(f_path: str = "config.json") -> Any:
    """
    Loads configuration from a json dictionary
    """
    with open(f_path, "r") as config_file:
        config = json.load(config_file)
    return config


def setup_argparse() -> Namespace:
    parser = ArgumentParser(
        description="Processes a file, outputs a script for imapsync",
        prog="pymap",
        epilog="The end",
    )
    parser.add_argument("host1", type=str, help="Origin hostname/IP")
    parser.add_argument("host2", type=str, help="Destination hostname/IP")
    parser.add_argument(
        "creds_file",
        type=str,
        help="Relative path to the file containing the users and credentials",
    )
    parser.add_argument(
        "-domain",
        "--domain",
        type=str,
        help="Domain to be used for the accounts if one is not provided in the file",
    )
    parser.add_argument(
        "-destination",
        "--destination",
        type=str,
        default="sync",
        help="Path to output file",
    )
    parser.add_argument(
        "-s",
        "--split",
        type=int,
        default=10,
        help="Specifies how many entries should each output contain",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default="INFO",
        help="Defines log level (INFO, WARNING, ERROR, DEBUG)",
    )
    parser.add_argument(
        "-c", "--config", default=None, help="Path of the configuration file"
    )
    parser.add_argument(
        "-dry",
        "--dry-run",
        action="store_true",
        default=False,
        help="Does not write to file only outputs debug",
    )
    args = parser.parse_args()
    return args


def verify_host(hostname: str, known_hosts: Optional[List[List[str]]] = None) -> str:
    """
    Verifies a hostname against a list of known host patterns.

    :param hostname: The hostname to check.
    :param known_hosts: A list of tuples (regex_pattern, append_string).
    :return: Modified hostname if matched, else original hostname.
    """
    logger.debug("Verifying hostname: %s", hostname)

    if known_hosts:
        for pattern, append_str in known_hosts:
            try:
                has_match = re.match(pattern, hostname)
                if has_match:
                    logger.debug("Matched hostname pattern: %s", pattern)
                    return f"{hostname}{append_str}"
            except Exception as e:
                logger.warning("Regex error in pattern %s: %s", pattern, e)
                continue

    logger.debug("No matches found for hostname: %s", hostname)
    return hostname
