param (
    [string]$ComPort = $null,
    [int]$BaudRate = 0
)

$IsGitHubActions = $env:GITHUB_ACTIONS -eq 'true'

# Use Python available in the CI environment
$PythonPath = "python"  # Use the global Python available in the CI environment

# Change to the project directory
Set-Location -Path (Join-Path -Path $PSScriptRoot -ChildPath "..\csad2425ki406shchyrbadv27")

Write-Output "Running software tests with coverage..."

# Run software tests with coverage
& coverage run -m pytest --junitxml=test-reports/results.xml "Tests_sw.py"

# If COM port and baud rate are specified, run hardware tests and append results to coverage data
if ($ComPort -ne $null -and $BaudRate -ne 0) {
    Write-Output "COM port $ComPort detected with baud rate $BaudRate. Running hardware tests..."

    # Run hardware tests via coverage
    & coverage run --append -m Tests_hw --port $ComPort --baudrate $BaudRate
} else {
    Write-Output "Skipping hardware tests because COM port or baud rate is not specified."
}

# Generate final coverage reports
Write-Output "Generating overall coverage report..."
& coverage combine  # Combine all collected coverage data
& coverage report   # Generate a text-based summary
& coverage html -d coverage_html_report  # Generate a single consolidated HTML report

Write-Output "Coverage report available in 'coverage_html_report/index.html'"
