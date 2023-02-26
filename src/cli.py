import logging
import sys
from core.pymap_core import ScriptGenerator
from core.tools import setup_argparse, set_logging, set_config


if __name__ == "__main__":
    args = setup_argparse()
    set_logging(args.log_level)
    config = set_config()

    options = {
        k: v for k, v in vars(args).items() if k not in ["host1", "host2", "creds_file"]
    }

    logging.debug(options)

    generator = ScriptGenerator(args.host1, args.host2, file_path=args.creds_file, **options)
    generator.process_file()
    sys.exit(0)
