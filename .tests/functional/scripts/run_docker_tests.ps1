# Configuration
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$REPORTS_DIR = "../reports"
$EVIDENCE_DIR = "../evidence"
$VERIFICATION_DIR = "../reports/verification"
$CERTIFICATION_DIR = "../reports/certification"
$COMPLETE_DIR = "../.complete"

# Create necessary directories
New-Item -ItemType Directory -Force -Path $REPORTS_DIR
New-Item -ItemType Directory -Force -Path $EVIDENCE_DIR
New-Item -ItemType Directory -Force -Path $VERIFICATION_DIR
New-Item -ItemType Directory -Force -Path $CERTIFICATION_DIR
New-Item -ItemType Directory -Force -Path $COMPLETE_DIR

# Function to log messages
function Log-Message {
    param($Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# Function to verify test results
function Verify-Results {
    param(
        [string]$TestName,
        [string]$ReportFile
    )

    Log-Message "Verifying results for $TestName..."

    # Check if test passed
    $reportContent = Get-Content $ReportFile -Raw
    if (-not ($reportContent -match "FAILED")) {
        # Check coverage
        if ($reportContent -match "TOTAL.+?(\d+)%") {
            $coverage = [int]$Matches[1]
            if ($coverage -ge 90) {
                Log-Message "Test $TestName passed with $coverage% coverage"
                return $true
            } else {
                Log-Message "Test $TestName failed coverage requirement: $coverage%"
                return $false
            }
        }
    }
    Log-Message "Test $TestName failed"
    return $false
}

# Function to move verified items to .complete
function Move-ToComplete {
    param(
        [string]$TestName,
        [string]$Timestamp
    )

    Log-Message "Moving $TestName to .complete..."

    # Create completion record
    $completionRecord = @{
        test_name = $TestName
        timestamp = $Timestamp
        status = "completed"
        verification_report = "${TestName}_verification_${Timestamp}.json"
        test_report = "${TestName}_report_${Timestamp}.html"
        coverage_report = "coverage/index.html"
    } | ConvertTo-Json

    Set-Content -Path "$COMPLETE_DIR/${TestName}_complete_${Timestamp}.json" -Value $completionRecord

    # Copy evidence and reports
    Copy-Item -Path "$REPORTS_DIR/${TestName}_report_${Timestamp}.html" -Destination "$COMPLETE_DIR/reports/" -Force
    Copy-Item -Path "$REPORTS_DIR/coverage" -Destination "$COMPLETE_DIR/reports/" -Recurse -Force
    Copy-Item -Path "$EVIDENCE_DIR/${TestName}_*" -Destination "$COMPLETE_DIR/evidence/" -Force -ErrorAction SilentlyContinue
}

# Main test execution
function Main {
    Log-Message "Starting test execution..."

    # Build and start services
    Log-Message "Building Docker services..."
    docker-compose -f ../docker-compose.test.yml build

    Log-Message "Starting services..."
    docker-compose -f ../docker-compose.test.yml up -d

    # Wait for services to be ready
    Log-Message "Waiting for services to be ready..."
    Start-Sleep -Seconds 10

    # Run API tests
    Log-Message "Running API tests..."
    docker-compose -f ../docker-compose.test.yml run --rm test-runner `
        python -m pytest tests/functional/api/test_api_endpoints.py `
        -v `
        --cov=app `
        --cov-report=term-missing `
        --cov-report=html:reports/coverage `
        --html=reports/api_test_report_${TIMESTAMP}.html `
        --self-contained-html `
        --junitxml=reports/api_test_${TIMESTAMP}.xml

    # Verify API test results
    if (Verify-Results "api" "reports/api_test_report_${TIMESTAMP}.html") {
        Move-ToComplete "api" $TIMESTAMP
    } else {
        Log-Message "API tests failed verification"
        exit 1
    }

    # Run security tests
    Log-Message "Running security tests..."
    docker-compose -f ../docker-compose.test.yml run --rm test-runner `
        python -m pytest tests/functional/test_security.py `
        -v `
        --cov=app `
        --cov-report=term-missing `
        --cov-report=html:reports/coverage `
        --html=reports/security_test_report_${TIMESTAMP}.html `
        --self-contained-html `
        --junitxml=reports/security_test_${TIMESTAMP}.xml

    # Verify security test results
    if (Verify-Results "security" "reports/security_test_report_${TIMESTAMP}.html") {
        Move-ToComplete "security" $TIMESTAMP
    } else {
        Log-Message "Security tests failed verification"
        exit 1
    }

    # Run chaos tests
    Log-Message "Running chaos tests..."
    docker-compose -f ../docker-compose.test.yml run --rm test-runner `
        python -m pytest tests/functional/test_chaos.py `
        -v `
        --cov=app `
        --cov-report=term-missing `
        --cov-report=html:reports/coverage `
        --html=reports/chaos_test_report_${TIMESTAMP}.html `
        --self-contained-html `
        --junitxml=reports/chaos_test_${TIMESTAMP}.xml

    # Verify chaos test results
    if (Verify-Results "chaos" "reports/chaos_test_report_${TIMESTAMP}.html") {
        Move-ToComplete "chaos" $TIMESTAMP
    } else {
        Log-Message "Chaos tests failed verification"
        exit 1
    }

    # Run ACID tests
    Log-Message "Running ACID tests..."
    docker-compose -f ../docker-compose.test.yml run --rm test-runner `
        python -m pytest tests/functional/test_acid.py `
        -v `
        --cov=app `
        --cov-report=term-missing `
        --cov-report=html:reports/coverage `
        --html=reports/acid_test_report_${TIMESTAMP}.html `
        --self-contained-html `
        --junitxml=reports/acid_test_${TIMESTAMP}.xml

    # Verify ACID test results
    if (Verify-Results "acid" "reports/acid_test_report_${TIMESTAMP}.html") {
        Move-ToComplete "acid" $TIMESTAMP
    } else {
        Log-Message "ACID tests failed verification"
        exit 1
    }

    # Generate final summary
    Log-Message "Generating final summary..."
    $summary = @{
        timestamp = $TIMESTAMP
        completed_tests = @("api", "security", "chaos", "acid")
        status = "completed"
        reports = @{
            api = "reports/api_test_report_${TIMESTAMP}.html"
            security = "reports/security_test_report_${TIMESTAMP}.html"
            chaos = "reports/chaos_test_report_${TIMESTAMP}.html"
            acid = "reports/acid_test_report_${TIMESTAMP}.html"
        }
    } | ConvertTo-Json

    Set-Content -Path "$COMPLETE_DIR/summary_${TIMESTAMP}.json" -Value $summary

    Log-Message "Test execution completed successfully"
}

# Run main function
Main
