import sys
import os
import logging
from logging.config import dictConfig
from core.pymap_core import ScriptGenerator
from core.tools import setup_argparse, set_logging, load_config

logger = logging.getLogger("PymapCLI")

if __name__ == "__main__":
    args = setup_argparse()
    config = {}
    if args.config and os.path.isfile(args.config):
        config = load_config(args.config)
    elif os.path.isfile("config.json"):
        config = load_config()
    if "LOGGING" in config:
        dictConfig(config["LOGGING"])
    else:
        set_logging(args.log_level)

    logger.info("Initialized PymapCLI logger")

    options = {
        k: v
        for k, v in vars(args).items()
        if k not in ["host1", "host2", "creds_file", "config"]
    }

    logger.debug("User options: %s", options)

    generator = ScriptGenerator(args.host1, args.host2, config=config, **options)
    try:
        generator.process_file(args.creds_file)
    except Exception as e:
        logger.critical("Unhandled exception occured: %s", e, exc_info=True)
        raise e
    sys.exit(0)
