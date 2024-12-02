# Define paths
$doxygenInstallerUrl = "https://doxygen.nl/files/doxygen-1.12.0-setup.exe" # Replace with the latest version if needed
# Use a more appropriate path for Linux
$doxygenInstallerPath = "/tmp/doxygen-setup.exe"
$projectDir = Join-Path -Path $PSScriptRoot -ChildPath ".." # Replace with the path to your project
$outputDir = "$projectDir\docs" # Path for generated documentation

# Step 1: Check if Doxygen is installed
Write-Output "Checking if Doxygen is installed..."
$doxygenPath = (Get-Command "doxygen" -ErrorAction SilentlyContinue).Source

if (-not $doxygenPath) {
    Write-Output "Doxygen not found. Downloading and installing Doxygen..."

    # Download Doxygen installer to /tmp (Linux-compatible path)
    Invoke-WebRequest -Uri $doxygenInstallerUrl -OutFile $doxygenInstallerPath -UseBasicParsing

    # Run the installer silently
    Start-Process -FilePath $doxygenInstallerPath -ArgumentList "/S" -Wait

    # Confirm installation
    $doxygenPath = (Get-Command "doxygen" -ErrorAction SilentlyContinue).Source
    if (-not $doxygenPath) {
        Write-Output "Doxygen installation failed. Please install it manually."
        exit 1
    }

    Write-Output "Doxygen installed successfully."
} else {
    Write-Output "Doxygen is already installed at $doxygenPath."
}

# Step 2: Create Doxygen configuration file if not exists
$doxyfilePath = "$projectDir\Doxyfile"
if (-not (Test-Path $doxyfilePath)) {
    Write-Output "Generating Doxygen configuration file..."
    Start-Process -FilePath "doxygen" -ArgumentList "-g $doxyfilePath" -Wait
}

# Step 3: Update configuration file for your project settings
(Get-Content $doxyfilePath) -replace 'OUTPUT_DIRECTORY.*', "OUTPUT_DIRECTORY = $outputDir" | Set-Content $doxyfilePath
(Get-Content $doxyfilePath) -replace 'INPUT.*', "INPUT = $projectDir" | Set-Content $doxyfilePath
(Get-Content $doxyfilePath) -replace 'RECURSIVE.*', "RECURSIVE = YES" | Set-Content $doxyfilePath

# Step 4: Run Doxygen to generate documentation
Write-Output "Generating documentation..."
Start-Process -FilePath "doxygen" -ArgumentList "$doxyfilePath" -Wait

Write-Output "Documentation generation complete. Output available at $outputDir."
