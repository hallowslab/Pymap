import re
from typing import Dict

LOGFILE_REGEX = re.compile(
    r"^(?P<source>[a-z0-9\-.]*)_(?P<dest>[a-z0-9\-.]*)_(?P<user1>[a-z0-9\-.@]*\.[a-z]{1,5})-(?P<user2>[a-z0-9\-.@]*)\.log$"
)

DATE_REGEX = re.compile(
    r".*(?P<time>[1-2][0-9]{3}-[0-1][0-9]-[0-3][0-9]\s[0-2][0-9]:[0-6][0-9]:[0-6][0-9]).*"
)

SPAM_ERROR = re.compile(
    r"Err [0-9]{1,3}/[0-9]{1,3}.* Folder (INBOX|Inbox|inbox)\.(spam|Spam|SPAM).*"
)

# DavMail settings, see http://davmail.sourceforge.net/ for documentation
DAVMAIL_PROPERTIES: str = """
davmail.server=true
davmail.mode=EWS
davmail.url=
davmail.caldavPort=
davmail.imapPort=
davmail.ldapPort=
davmail.popPort=
davmail.smtpPort=
davmail.enableProxy=false
davmail.useSystemProxies=false
davmail.proxyHost=
davmail.proxyPort=
davmail.proxyUser=
davmail.proxyPassword=
davmail.noProxyFor=
davmail.allowRemote=true
davmail.bindAddress=
davmail.clientSoTimeout=
davmail.ssl.keystoreType=
davmail.ssl.keystoreFile=
davmail.ssl.keystorePass=
davmail.ssl.keyPass=
davmail.server.certificate.hash=
davmail.ssl.nosecurecaldav=false
davmail.ssl.nosecureimap=false
davmail.ssl.nosecureldap=false
davmail.ssl.nosecurepop=false
davmail.ssl.nosecuresmtp=false
davmail.disableUpdateCheck=true
davmail.enableKeepalive=false
davmail.folderSizeLimit=0
davmail.defaultDomain=
davmail.caldavAlarmSound=
davmail.caldavPastDelay=90
davmail.caldavAutoSchedule=true
davmail.forceActiveSyncUpdate=false
davmail.imapAutoExpunge=true
davmail.imapIdleDelay=
davmail.keepDelay=30
davmail.sentKeepDelay=90
davmail.popMarkReadOnRetr=false
davmail.smtpSaveInSent=true
davmail.logFilePath=/var/log/davmail.log
davmail.logFileSize=1MB
log4j.logger.davmail=WARN
log4j.logger.httpclient.wire=WARN
log4j.logger.org.apache.commons.httpclient=WARN
log4j.rootLogger=WARN
davmail.ssl.pkcs11Config=
davmail.ssl.pkcs11Library=
davmail.ssl.clientKeystoreType=
davmail.ssl.clientKeystoreFile=
davmail.ssl.clientKeystorePass=
davmail.disableGuiNotifications=false
davmail.disableTrayActivitySwitch=false
davmail.showStartupBanner=true
davmail.enableKerberos=false
"""

"""
0 OK
1 CATCH_ALL
6 EXIT_SIGNALLED
7 EXIT_BY_FILE
8 EXIT_PID_FILE_ERROR
10 EXIT_CONNECTION_FAILURE
12 EXIT_TLS_FAILURE
16 EXIT_AUTHENTICATION_FAILURE
21 EXIT_SUBFOLDER1_NO_EXISTS
111 EXIT_WITH_ERRORS
112 EXIT_WITH_ERRORS_MAX
113 EXIT_OVERQUOTA
114 EXIT_ERR_APPEND
115 EXIT_ERR_FETCH
116 EXIT_ERR_CREATE
117 EXIT_ERR_SELECT
118 EXIT_TRANSFER_EXCEEDED
119 EXIT_ERR_APPEND_VIRUS
254 EXIT_TESTS_FAILED
101 EXIT_CONNECTION_FAILURE_HOST1
102 EXIT_CONNECTION_FAILURE_HOST2
161 EXIT_AUTHENTICATION_FAILURE_USER1
162 EXIT_AUTHENTICATION_FAILURE_USER2
64 BAD_USAGE
66 NO_INPUT
69 SERVICE_UNAVAILABLE
70 INTERNAL_SOFTWARE_ERROR
"""
IMAPSYNC_CODES: Dict[str, str] = {
    "0": "✅",
    "1": "⚠ CatchAll",
    "6": "⚠ received Exit signal",
    "7": "⚠ Exit By File",
    "8": "⚠ Exit PID File Error",
    "10": "⛔Connection failure",
    "12": "⛔TLS Failure",
    "16": "⛔Authentication Failure",
    "21": "⚠ Subfolder 1 Does not exist",
    "111": "⚠ Exit With Errors",
    "112": "❌Reached max Errors",
    "113": "❌Reached max quota",
    "114": "📤Failed to append file or directory",
    "115": "📤Failed to fetch",
    "116": "📤Failed to create file/folder",
    "117": "⚠ Failed to select file/folder",
    "118": "❌Transfer exceeded",
    "119": "📥Failed to append, possible virus",
    "254": "⚠ Tests failed",
    "101": "📤Failed to connect on host1",
    "102": "📥Failed to connect on host2",
    "161": "📤Failed to authenticate user1",
    "162": "📥Failed to authenticate user2",
    "64": "❌Bad usage, possible invalid argument",
    "66": "❌Received no input",
    "69": "⚠ Service unavalilable?",
    "70": "❌ Internal Software error",
}
