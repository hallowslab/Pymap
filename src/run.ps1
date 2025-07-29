param(
    [Parameter()]
    [switch]$Help,

    [Parameter(Mandatory=$true)]
    [string]$DjangoEnv,

    [Parameter(Mandatory=$true)]
    [string]$DjangoConfigFile,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Display help if -Help is provided
if ($Help) {
    Write-Host "Usage: script.ps1 -DjangoEnv <value> -DjangoConfigFile <value> [args...]"
    Write-Host "  -DjangoEnv: The environment to use (e.g., 'development', 'production')"
    Write-Host "  -DjangoConfigFile: The path to the Django config file"
    Write-Host "  [args...]: Optional arguments to pass to the command"
    Write-Host "Usage Examples:"
    Write-Host "  Interacting with django"
    Write-Host "    script.ps1 development ..\secrets\config.dev.json python manage.py ...."
    Write-Host "  Running tasks"
    Write-Host "    script.ps1 development ..\secrets\config.dev.json task format"
    exit
}

# Set environment variables
$env:DJANGO_ENV = $DjangoEnv
$env:DJANGO_CONFIG_FILE = $DjangoConfigFile

# Build the command as an array
$cmd = @('poetry', 'run') + $Args

# Print what will be run
Write-Host "Running with:"
Write-Host "  DJANGO_ENV=$DjangoEnv"
Write-Host "  DJANGO_CONFIG_FILE=$DjangoConfigFile"
Write-Host "  Command: $($cmd -join ' ')"

# Run the command
& $cmd[0] $cmd[1..($cmd.Length - 1)]
if ($LASTEXITCODE -ne 0) {
    Write-Error "Command failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}