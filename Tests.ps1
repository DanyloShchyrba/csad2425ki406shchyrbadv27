# ------------------------- CONFIGURABLE VARIABLES -----------------------------------------
param (
    [string]$port = "",
    [int]$baudRate = 0 
)

$board = "esp8266:esp8266:nodemcuv2"
$sketch = "TicTacToeHW/TicTacToeHW.ino"
$serialLog = "serial_output.log"
$pythonScript = "Game.py"
$exeFilePath = "Game.exe"
$pythonTestScript = "Tests_sw.py"  # Test script for Python logic
$pythonHWTestScript = "Tests_hw.py"  # Script for testing Arduino communication
$testResultsLog = "test_results.log"  # Log file for test results
# ------------------------------------------------------------------------------------------

# Check if the log file exists and clear it
if (Test-Path $testResultsLog) {
    Write-Host "Log file exists. Clearing the contents of $testResultsLog..."
    Clear-Content -Path $testResultsLog
} else {
    Write-Host "No log file found. Skipping clearance."
}

function Verify-ArduinoCLI {
    # Ensure the Arduino CLI is installed and available
    if (-not (Get-Command arduino-cli -ErrorAction SilentlyContinue)) {
        Write-Host "arduino-cli not detected. Please ensure it is installed."
        exit 1
    }
}

function Build-Sketch {
    # Compile the Arduino sketch
    Write-Host "Starting compilation of the Arduino sketch..."
    $compileCommand = & arduino-cli compile --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Compilation failed. Please check for issues in the code."
        exit 1
    }
    Write-Host "Compilation completed successfully."
}

function Flash-Sketch {
    # Upload the compiled sketch to the Arduino board
    Write-Host "Uploading the sketch to the ESP8266 via port $port..."
    & arduino-cli upload -p $port --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Upload failed. Review the output for possible errors."
        exit 1
    }
    Write-Host "Upload was successful."
}

function Create-Exe {
    # Generate an executable file from the Python script
    Write-Host "Generating an .exe file from the Python script $pythonScript..."
    $scriptDir = (Get-Location).Path
    & pyinstaller --onefile --distpath "$scriptDir" --workpath "$scriptDir/_build" --specpath "$scriptDir/_specs" $pythonScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Executable file created successfully: $exeFilePath"
    } else {
        Write-Host "Executable file creation failed. Investigate the issue."
        exit 1
    }
}

function Execute-PythonTests {
    # Execute Python logic tests
    Write-Host "Executing Python tests from $pythonTestScript..."
    & python $pythonTestScript
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python logic tests passed successfully."
    } else {
        Write-Host "Python logic tests failed. Check the logs for details."
        exit 1
    }
}

function Execute-HardwareTests {
    # Execute Arduino communication tests
    Write-Host "Running communication tests using $pythonHWTestScript..."
    Start-Sleep -Seconds 3
    & python $pythonHWTestScript $port $baudRate
    if ($LASTEXITCODE -eq 0) {
        Write-Host "UART communication tests passed successfully."
    } else {
        Write-Host "UART communication tests failed. Refer to the logs for further insights."
        exit 1
    }
}

# Always generate the EXE file
Create-Exe

# Perform Arduino operations only if port and baudRate are provided
if (-not [string]::IsNullOrEmpty($port) -and $baudRate -ne 0) {
    Verify-ArduinoCLI
    Build-Sketch
    Flash-Sketch
    Execute-HardwareTests
} else {
    Write-Host "Arduino parameters not provided. Skipping Arduino-related tasks."
}

# Run Python logic tests
Execute-PythonTests
