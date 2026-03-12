$ErrorActionPreference = "Stop"

function Get-PythonLauncher {
    foreach ($candidate in @("py", "python", "python3")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            return $candidate
        }
    }

    throw "Python was not found in PATH. Install Python or add it to PATH."
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-PythonLauncher

Write-Host "Starting Streamlit..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; & $python -m streamlit run streamlit/app.py"
)

Write-Host "Starting React..."
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; npm --prefix react-app start"
)

Write-Host ""
Write-Host "React: http://localhost:3000"
Write-Host "Streamlit: http://localhost:8501"
