class LogfileConverter:
    # The string format from the core
    # "{self.host1}__{self.host2}__{username1}--{username2}.log"
    regex: str = ".*__.*__.*--[^\/?]+"

    def to_python(self, value: str) -> str:
        return str(value)

    def to_url(self, value: str) -> str:
        return "%s" % value
