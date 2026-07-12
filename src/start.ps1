# start.ps1
# Setup environment for local n8n and Python scripts without Docker

# Load environment variables from .env if it exists
if (Test-Path "$PSScriptRoot\.env") {
    Write-Host "Loading environment variables from .env..." -ForegroundColor Cyan
    Get-Content "$PSScriptRoot\.env" | Foreach-Object {
        $line = $_.Trim()
        if ($line -and !$line.StartsWith("#") -and $line.Contains("=")) {
            $key, $value = $line -split '=', 2
            $key = $key.Trim()
            $value = $value.Trim()
            # Strip outer quotes if any
            if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Enforce local settings
$env:DATA_DIR = "D:/AI Job Automation"
$env:PYTHON_CMD = "$PSScriptRoot\..\.venv\Scripts\python.exe"

# Isolate n8n database and settings to local workspace folder
$env:N8N_USER_FOLDER = "$PSScriptRoot\..\.n8n"

# Allow executing commands and require modules in Code node
$env:NODE_FUNCTION_ALLOW_EXTERNAL = "fs,path"
$env:NODE_FUNCTION_ALLOW_BUILTIN = "fs,path"
$env:N8N_BLOCK_ENV_ACCESS_IN_NODE = "false"
$env:NODES_EXCLUDE = "[]"
$env:N8N_ENABLE_UNSAFE_CORE_NODES = "true"

# Add virtual environment script directory to PATH
$env:PATH = "$PSScriptRoot\..\.venv\Scripts;" + $env:PATH

# Create isolated .n8n folder if not exists
if (!(Test-Path "$PSScriptRoot\..\.n8n")) {
    New-Item -ItemType Directory -Path "$PSScriptRoot\..\.n8n" -Force | Out-Null
}

Write-Host "Starting n8n locally on port 5678..." -ForegroundColor Green
Write-Host "Data directory is configured as: $env:DATA_DIR" -ForegroundColor Green
Write-Host "Python environment path is: $env:PYTHON_CMD" -ForegroundColor Green

# Start n8n and redirect output to prevent terminal locks
n8n > "$PSScriptRoot\..\n8n_console.log" 2>&1
