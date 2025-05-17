import logging
from typing import Callable, List, TypedDict
from imaplib import IMAP4, IMAP4_SSL

logger = logging.getLogger("migrator.utilities.imap")

IMAPConstructor = Callable[..., IMAP4]


class IMAPConfig(TypedDict):
    function: IMAPConstructor
    port: int


def check_imap_id_support(host: str, timeout: int = 5) -> bool:
    configs: List[IMAPConfig] = [
        {"function": IMAP4_SSL, "port": 993},
        {"function": IMAP4, "port": 143},
    ]
    for config in configs:
        imap = None
        try:
            imap = config["function"](host, config["port"], timeout=timeout)
            _, data = imap.capability()
            capabilities = b" ".join(data).decode().upper().split()
            if "ID" in capabilities:
                return True
        # Ignore exceptions we handle closing in finally block
        except Exception:
            continue
        finally:
            if imap:
                # Attempt to close connection
                try:
                    imap.logout()
                except Exception as e:
                    logger.error(
                        f"Exception closing IMAP connection: {e}", exc_info=True
                    )
                    pass  # ignore logout errors
    return False
