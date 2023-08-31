import logging
import re
from typing import Generator, Iterable, List, Optional


# TODO: Pass this in trough parameters
LOGDIR = "/var/log/pymap"


class ScriptGenerator:
    USER_IDENTIFIER = re.compile(r"^[\w.]+(?P<mail_provider>@[\w.]+)*")
    PASS_IDENTIFIER = re.compile(r".*[\s|,|.]+(?P<pword>.+)$")
    # Finding a delimiter for the password can be difficult since passwords
    # can be made up of almost any character
    WHOLE_STRING_ID = re.compile(
        r"^(?P<user1>[\w.-]+)(?P<mail_provider1>@[\w.-]+)[ |,|\||\t]+(?P<pword1>.+)(?P<part2>[ |,|\||\t]+(?P<user2>[\w.-]+?)(?P<mail_provider2>@[\w.-]+)[ |,|\||\t]+(?P<pword2>.+))?$"
    )
    IP_ADDR_RE = re.compile(r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}")
    FORMAT_STRING = (
        "imapsync --host1 {} --user1 {} --password1 '{}' --host2 {}  --user2 {} --password2 '{}' --log --logdir="
        + LOGDIR
        + " --logfile={} --addheader"
    )

    def __init__(
        self,
        host1: str,
        host2: str,
        creds=None,
        file_path=None,
        extra_args: str = "",
        **kwargs,
    ) -> None:
        self.logger = logging.getLogger("PymapCore")
        # TODO: Cannot suply types : Optional[PathLike[str]] when using open
        self.file_path = file_path
        self.creds: Iterable = creds
        self.dest: str = kwargs.get("out_file", "sync")
        self.line_count: int = kwargs.get("split", 30)
        self.file_count: int = 0
        self.extra_args: Optional[str] = extra_args
        self.fallback_separator: str = kwargs.get("fallback_separator", "<->")
        # Load the config before matching hosts, since they are matched trough the strings defined
        # in the HOSTS section
        self.config = kwargs.get("config", {})
        self.host2: str = self.match_host(host2)
        self.host1: str = self.match_host(host1)

    # Verifies if the hostname is either a CPanel, Plesk or WEBLX instance
    # and returns the apropriate FQDN
    def match_host(self, hostname: str) -> str:
        if self.config and len(self.config.get("HOSTS", [])) > 1:
            # Fetch hosts from config
            all_hosts = self.config.get("HOSTS")
            all_hosts = {k: v for k, v in [x for x in all_hosts]}
            for k in all_hosts:
                has_match = re.match(k, hostname)
                if has_match and has_match.end() == len(hostname):
                    self.logger.debug("Matched hostname: %s", hostname)
                    return f"{hostname}{all_hosts[k]}"
        return hostname

    def process_file(self) -> None:
        if self.file_path is not None and self.file_path != "":
            try:
                lines = []
                with open(self.file_path, "r") as fh:
                    for line in self.line_generator(fh):
                        lines.append(line)
                        if len(lines) >= self.line_count:
                            self.write_output(lines)
                            lines.clear()
                    if len(lines) >= 1:
                        self.write_output(lines)
            except Exception as e:
                self.logger.critical(
                    "Unhandled exception: %s", e.__str__(), exc_info=True
                )
                raise
        else:
            raise ValueError(f"File path was not supplied: {self.file_path}")

    def process_string(self) -> List[str]:
        # TODO: Strip out passwords before logging commands
        # self.logger.debug("Supplied data: %s", self.creds)
        scripts = [x for x in self.line_generator(self.creds) if x is not None]
        return scripts

    # processes input -> yields str
    def line_generator(self, uinput: Iterable) -> Generator:
        new_line = None
        for line in uinput:
            if line and len(line) > 1:
                # Process line
                new_line = self.parse_line(line)
                if new_line:
                    # if extra arguments append at end
                    if self.extra_args:
                        new_line = f"{new_line} {self.extra_args}"
                    yield new_line

    # Parses individual Lines returns None or a formatted string
    def parse_line(self, line: str) -> Optional[str]:
        # FIXME: Remove passwords before logging
        self.logger.debug("Parsing Line %s....", line[0:5])
        has_match = re.match(self.WHOLE_STRING_ID, line)
        # FIXME: Regex has catastrophic backtracing, should not be used for now...
        # TODO: Maybe replace regex for the splitting logic
        if has_match:
            user1 = has_match.group("user1")
            user2 = has_match.group("user2")
            mail1 = has_match.group("mail_provider1")
            mail2 = has_match.group("mail_provider2")
            self.logger.debug(f"Adding task: {user1}{mail1} -> {user2}{mail2}")
            self.logger.debug(
                f"\nUSER1:{user1}\tUSER2:{user2}\tMAIL1{mail1}\tMAIL2{mail2}"
            )
            username1: Optional[str] = f"{user1}{mail1}" if mail1 else None
            username2: Optional[str] = f"{user2}{mail2}" if mail2 else None
            if username1:
                return self.FORMAT_STRING.format(
                    self.host1,
                    username1,
                    has_match.group("pword1"),
                    self.host2,
                    username1,
                    has_match.group("pword2"),
                    f"{self.host1}__{self.host2}__{username1}--{username1}.log",
                )
            elif username1 and username2:
                return self.FORMAT_STRING.format(
                    self.host1,
                    username1,
                    has_match.group("pword1"),
                    self.host2,
                    username2,
                    has_match.group("pword2"),
                    f"{self.host1}__{self.host2}__{username1}--{username2}.log",
                )
            else:
                self.logger.warning("User missing domain or provider")
        else:
            self.logger.warning("Line did not match regex %s....", line)
            try:
                new_line = re.sub("\t+", " ", line)
                new_line = re.sub("\s+", " ", new_line)
                new_line_split: List[str] = new_line.split(self.fallback_separator)
                if len(new_line_split) > 1:
                    user1 = new_line_split[0]
                    pword1 = new_line_split[1]
                    user2 = new_line_split[0]
                    pword2 = new_line_split[1]
                    if len(new_line_split) >= 4:
                        user2 = new_line_split[2]
                        pword2 = new_line_split[3]
                    self.logger.info("Line %s Matched trough fallback", line[0:5])
                    return self.FORMAT_STRING.format(
                        self.host1,
                        user1,
                        pword1,
                        self.host2,
                        user2,
                        pword2,
                        f"{self.host1}__{self.host2}__{user1}--{user2}.log",
                    )
            except Exception as e:
                self.logger.error("Line did not match split %s", line[0:5])
                self.logger.error("Error: %s", e)
                return None
        return None

    # Writes output to a file
    def write_output(self, lines: List[str]) -> None:
        dest = f"{self.dest}_{self.file_count}.sh"
        self.logger.debug("Writting %s lines to file %s", len(lines), dest)
        lines = [line + "\n" for line in lines]
        with open(dest, "w") as fh:
            fh.writelines(lines)
        self.file_count += 1
