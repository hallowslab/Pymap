param(
    [Parameter(Mandatory=$true)]
    [string]$DjangoEnv,

    [Parameter(Mandatory=$true)]
    [string]$DjangoConfigFile,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Set environment variables
$env:DJANGO_ENV = $DjangoEnv
$env:DJANGO_CONFIG_FILE = $DjangoConfigFile

# Build the command as an array
$cmd = @('poetry', 'run', 'python', 'manage.py') + $Args

# Print what will be run
Write-Host "Running with:"
Write-Host "  DJANGO_ENV=$DjangoEnv"
Write-Host "  DJANGO_CONFIG_FILE=$DjangoConfigFile"
Write-Host "  Command: $($cmd -join ' ')"

# Run the command
& $cmd[0] $cmd[1..($cmd.Length - 1)]
