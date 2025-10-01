# Server-to-Server FTP Transfer via PHP Script: A Step-by-Step Guide
## Objective
Transfer files from a source FTP server to a destination webserver's public_html directory without using disk space or RAM on the local machine running the Python app.

This guide describes a secure, automated workflow where the Python app prepares and deploys a PHP transfer script to one of the servers, and that script handles the server-to-server file transfer.

## Why This Approach?
- No local resource consumption
- Bypasses FXP restrictions and RAM limits
- Requires only FTP and HTTP access (no SSH needed)
- Minimizes attack surface by avoiding URL-based credentials

### Step 1: Prepare the PHP Transfer Template
Create a PHP template script with placeholders for sensitive data.

```
Template Placeholders - Placeholder	Description
{{TOKEN}}       Secure execution token
{{FTP_FTP}}	    FTP host
{{FTP_USER}}	FTP username
{{FTP_PASS}}	FTP password
{{FTP_PATH}}	Directory to copy (e.g., /public_html)
```

### Step 2: Python Templating and Script Generation
Use the Python app to populate the template at runtime.

Tasks:
Replace placeholders with actual values.

Generate a unique transfer.php script per transfer to avoid re-use risks.

Example
```python
php_template = open('transfer_template.php').read()

script = php_template \
    .replace('{{TOKEN}}', 'secure_random_token_1234') \
    .replace('{{FTP_SERVER}}', 'ftp.server.com') \
    .replace('{{FTP_USER}}', 'ftpuser') \
    .replace('{{FTP_PASS}}', 'ftppass') \
    .replace('{{REMOTE_PATH}}', '/public_html')

with open('transfer.php', 'w') as f:
    f.write(script)
```

### Step 3: Upload the Script to the Server
Use Python's ftplib to upload transfer.php to the webserver's public_html (or a subdirectory):

```python
from ftplib import FTP

ftp = FTP('example-server.com')
ftp.login('ftp_user', 'ftp_pass')

with open('transfer.php', 'rb') as f:
    ftp.storbinary('STOR transfer.php', f)

ftp.quit()
```

### Step 4: Execute the Transfer Script Securely
Use HTTPS POST + Authorization header to trigger the script:

Example Request
```python
import requests

headers = {
    'Authorization': 'Bearer secure_random_token_1234'
}

response = requests.post('https://example-server.com/transfer.php', headers=headers)

print(response.text)
```

### Step 5: Optional Cleanup
For security, delete the transfer script after execution.

- Option 1: Self-deleting PHP
Add at the end of transfer.php:

```php
unlink(__FILE__);
```

- Option 2: Python Cleanup
Use ftplib to remove transfer.php after confirming success:

```python
ftp = FTP('example-server.com')
ftp.login('user', 'pass')
ftp.delete('transfer.php')
ftp.quit()
```

### Step 6: Security Best Practices
Concern	Mitigation
Credential leakage	Never pass FTP creds via URL
Token hijacking	Use HTTPS and header-based auth
Script re-use risk	Use one-time unique tokens and per-transfer scripts
Exposure risk	Upload script only when needed and delete immediately after use
IP restriction (optional)	Add IP whitelisting in the PHP script

### Step 7: Error Handling & Monitoring
Recommended Practices
Log transfer progress to STDOUT or a log file.

Return detailed HTTP responses for success/failure.

Use retries or fallback mechanisms in the Python controller.

## Summary: Full Workflow
```mermaid
flowchart TD
    A[Python App] -->|Templating| B[Generated transfer.php]
    B -->|Upload via FTP| C[(Source|Destination) Webserver]
    A -->|Trigger via HTTPS POST| C
    C -->|FTP (upload|download) from (Source|Destination)| D[(Source|Destination) FTP Server]
    C -->|Writes to public_html| E[Destination Filesystem]
    C -->|Optional cleanup| F[Delete transfer.php]
```
Benefits of This Approach
Resource-safe: No RAM/disk overhead on Python app server

Flexible: Works in shared hosting/webserver-only environments

Secure: Uses header-based auth and removes scripts after execution

Automated: Fully controlled by the Python application

### Next Steps
Implement the Python control logic for template rendering, FTP upload, execution, and cleanup.

Test in a controlled environment before production use.

Harden the PHP script further if needed (e.g., add logging, IP restrictions, file type filters).