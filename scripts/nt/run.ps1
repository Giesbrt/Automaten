# Disable PowerShell output buffering for real-time echoing
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Installing/Checking Packages ..."
# Check for Freeze_versions?
py -3.12 -m pip install -r requirements.txt | Out-Null

# Navigate to the 'src' directory
Set-Location -Path "src"

# Run the main Python script
py -3.12 ./main.py

Set-Location -Path ".."

# Pause equivalent
Read-Host -Prompt "Press Enter to continue..."
