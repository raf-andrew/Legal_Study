# Route Test Runner
# Manages and executes all route tests in the system

param(
    [string]$RouteName,
    [string]$Category,
    [switch]$All,
    [switch]$GenerateReport,
    [switch]$UpdateMaster
)

# Configuration
$ROUTES_DIR = ".codespaces/routes"
$MASTER_ROUTES = "$ROUTES_DIR/master_routes.json"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$REPORT_DIR = "$ROUTES_DIR/reports"

# Ensure report directory exists
if (-not (Test-Path $REPORT_DIR)) {
    New-Item -ItemType Directory -Path $REPORT_DIR | Out-Null
}

# Load master routes
$masterRoutes = Get-Content $MASTER_ROUTES | ConvertFrom-Json

# Initialize test report
$testReport = @{
    timestamp = $TIMESTAMP
    test_name = "Route Test Run"
    status = "running"
    results = @{}
    summary = @{
        total_routes = 0
        passed_routes = 0
        failed_routes = 0
        skipped_routes = 0
    }
}

function Test-SingleRoute {
    param(
        [string]$RouteName,
        [string]$Category
    )

    $routePath = "$ROUTES_DIR/$Category/$RouteName"
    $testScript = "$routePath/tests/test.ps1"

    if (-not (Test-Path $testScript)) {
        Write-Warning "No test script found for route: $Category/$RouteName"
        return @{
            status = "skipped"
            message = "No test script found"
        }
    }

    try {
        # Execute test script
        & $testScript
        $result = @{
            status = "passed"
            message = "Test completed successfully"
            report = "$routePath/tests/reports/${RouteName}_test.json"
        }
    }
    catch {
        $result = @{
            status = "failed"
            message = $_.Exception.Message
            report = "$routePath/tests/reports/${RouteName}_test.json"
        }
    }

    return $result
}

function Test-Category {
    param(
        [string]$Category
    )

    $categoryResults = @{
        status = "running"
        routes = @{}
    }

    foreach ($route in $masterRoutes.routes.$Category.PSObject.Properties) {
        $routeName = $route.Name
        $result = Test-SingleRoute -RouteName $routeName -Category $Category
        $categoryResults.routes[$routeName] = $result
    }

    $categoryResults.status = if ($categoryResults.routes.Values.Status -contains "failed") { "failed" } else { "passed" }
    return $categoryResults
}

function Update-MasterRoutes {
    param(
        [hashtable]$TestResults
    )

    foreach ($category in $TestResults.results.Keys) {
        foreach ($route in $TestResults.results[$category].routes.Keys) {
            $result = $TestResults.results[$category].routes[$route]
            $masterRoutes.routes.$category.$route.test_status = $result.status
            $masterRoutes.routes.$category.$route.test_report = $result.report
        }
    }

    $masterRoutes | ConvertTo-Json -Depth 10 | Set-Content $MASTER_ROUTES
}

# Main execution
if ($All) {
    # Test all routes
    foreach ($category in $masterRoutes.categories.PSObject.Properties) {
        $categoryName = $category.Name
        $testReport.results[$categoryName] = Test-Category -Category $categoryName
    }
}
elseif ($Category) {
    # Test specific category
    $testReport.results[$Category] = Test-Category -Category $Category
}
elseif ($RouteName) {
    # Test specific route
    $category = $masterRoutes.routes.PSObject.Properties |
        Where-Object { $_.Value.PSObject.Properties.Name -contains $RouteName } |
        Select-Object -ExpandProperty Name

    if ($category) {
        $testReport.results[$category] = @{
            status = "running"
            routes = @{
                $RouteName = (Test-SingleRoute -RouteName $RouteName -Category $category)
            }
        }
    }
    else {
        Write-Error "Route not found: $RouteName"
        exit 1
    }
}

# Calculate summary
$testReport.summary.total_routes = ($testReport.results.Values |
    ForEach-Object { $_.routes.Count } |
    Measure-Object -Sum).Sum

$testReport.summary.passed_routes = ($testReport.results.Values |
    ForEach-Object { $_.routes.Values | Where-Object { $_.status -eq "passed" } } |
    Measure-Object).Count

$testReport.summary.failed_routes = ($testReport.results.Values |
    ForEach-Object { $_.routes.Values | Where-Object { $_.status -eq "failed" } } |
    Measure-Object).Count

$testReport.summary.skipped_routes = ($testReport.results.Values |
    ForEach-Object { $_.routes.Values | Where-Object { $_.status -eq "skipped" } } |
    Measure-Object).Count

# Set overall status
$testReport.status = if ($testReport.summary.failed_routes -gt 0) { "failed" } else { "passed" }

# Generate report if requested
if ($GenerateReport) {
    $reportPath = "$REPORT_DIR/test_run_$TIMESTAMP.json"
    $testReport | ConvertTo-Json -Depth 10 | Set-Content $reportPath
    Write-Host "Test report generated: $reportPath"
}

# Update master routes if requested
if ($UpdateMaster) {
    Update-MasterRoutes -TestResults $testReport
    Write-Host "Master routes updated"
}

# Output summary
Write-Host "`nTest Run Summary:"
Write-Host "Total Routes: $($testReport.summary.total_routes)"
Write-Host "Passed: $($testReport.summary.passed_routes)"
Write-Host "Failed: $($testReport.summary.failed_routes)"
Write-Host "Skipped: $($testReport.summary.skipped_routes)"
Write-Host "Overall Status: $($testReport.status)"

# Exit with appropriate code
if ($testReport.status -eq "failed") {
    exit 1
}
exit 0
