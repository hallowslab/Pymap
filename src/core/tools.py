import logging
import argparse
import configparser


def set_config(f_path="config.ini"):
    config = configparser.ConfigParser()
    config.read(f_path)
    return config


# Try to parse log level, default to 20/INFO
def set_logging(log_level):
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


def setup_argparse():
    parser = argparse.ArgumentParser(
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
        "-dry",
        "--dry-run",
        action="store_true",
        default=False,
        help="Does not write to file only outputs debug",
    )
    args = parser.parse_args()
    return args
