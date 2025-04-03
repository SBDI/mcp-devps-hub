# PowerShell script to run the MCP DevOps Hub demo with server and client
# This script opens two terminal windows - one for the server and one for the client

# Function to activate virtual environment and run a command
function Invoke-InVirtualEnv {
    param (
        [string]$Command
    )
    
    # Construct the full command with virtual environment activation
    $fullCommand = "& {
        # Activate virtual environment
        & '.\.venv\Scripts\Activate.ps1'
        
        # Run the command
        $Command
        
        # Keep the window open
        Write-Host `"`nPress any key to close...`"
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }"
    
    # Return the PowerShell command to execute
    return $fullCommand
}

# Get the current directory
$currentDir = Get-Location

Write-Host "Starting MCP DevOps Hub Demo..." -ForegroundColor Green
Write-Host "This will open two terminal windows:" -ForegroundColor Yellow
Write-Host "1. MCP DevOps Hub Server" -ForegroundColor Yellow
Write-Host "2. MCP Client Demo" -ForegroundColor Yellow
Write-Host ""

# Start the MCP DevOps Hub server in a new window
$serverCommand = Invoke-InVirtualEnv -Command "mcp-devops-hub"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $serverCommand -WindowStyle Normal

# Wait for the server to start
Write-Host "Starting server..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
Write-Host "Server should be running now." -ForegroundColor Green

# Start the client demo in a new window
$clientCommand = Invoke-InVirtualEnv -Command "python scripts\mcp_client_demo.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $clientCommand -WindowStyle Normal

Write-Host "Demo started!" -ForegroundColor Green
Write-Host "- Server is running in the first terminal window" -ForegroundColor Cyan
Write-Host "- Client demo is running in the second terminal window" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now interact with the client to demonstrate the MCP DevOps Hub functionality." -ForegroundColor Yellow
Write-Host "When finished, close both terminal windows." -ForegroundColor Yellow
