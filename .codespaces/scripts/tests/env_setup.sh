#!/bin/bash

# Environment Setup Test Script
# Tests the Codespaces environment initialization and configuration

# Configuration
REPORT_FILE=".codespaces/complete/testing/env_setup.json"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Initialize report
echo "{" > "${REPORT_FILE}"
echo "  \"timestamp\": \"${TIMESTAMP}\"," >> "${REPORT_FILE}"
echo "  \"test_name\": \"Environment Setup\"," >> "${REPORT_FILE}"
echo "  \"status\": \"running\"," >> "${REPORT_FILE}"
echo "  \"results\": {" >> "${REPORT_FILE}"

# Test environment variables
echo "    \"environment_variables\": {" >> "${REPORT_FILE}"
required_vars=("CODESPACE_NAME" "GITHUB_TOKEN" "DATABASE_URL" "API_KEY")
all_vars_present=true

for var in "${required_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "      \"${var}\": \"configured\"," >> "${REPORT_FILE}"
    else
        echo "      \"${var}\": \"missing\"," >> "${REPORT_FILE}"
        all_vars_present=false
    fi
done

if [ "$all_vars_present" = false ]; then
    echo "      \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "      \"error\": \"Missing required environment variables\"" >> "${REPORT_FILE}"
    echo "    }," >> "${REPORT_FILE}"
    echo "  \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "  \"error\": \"Environment setup verification failed\"" >> "${REPORT_FILE}"
    echo "}" >> "${REPORT_FILE}"
    exit 1
fi

echo "      \"status\": \"passed\"" >> "${REPORT_FILE}"
echo "    }," >> "${REPORT_FILE}"

# Test network connectivity
echo "    \"network_connectivity\": {" >> "${REPORT_FILE}"
endpoints=("api.github.com" "database.internal" "cache.internal")
all_endpoints_reachable=true

for endpoint in "${endpoints[@]}"; do
    if ping -n 1 "${endpoint}" > /dev/null 2>&1; then
        echo "      \"${endpoint}\": \"reachable\"," >> "${REPORT_FILE}"
    else
        echo "      \"${endpoint}\": \"unreachable\"," >> "${REPORT_FILE}"
        all_endpoints_reachable=false
    fi
done

if [ "$all_endpoints_reachable" = false ]; then
    echo "      \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "      \"error\": \"Some endpoints are unreachable\"" >> "${REPORT_FILE}"
    echo "    }," >> "${REPORT_FILE}"
    echo "  \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "  \"error\": \"Network connectivity verification failed\"" >> "${REPORT_FILE}"
    echo "}" >> "${REPORT_FILE}"
    exit 1
fi

echo "      \"status\": \"passed\"" >> "${REPORT_FILE}"
echo "    }," >> "${REPORT_FILE}"

# Test file system access
echo "    \"file_system\": {" >> "${REPORT_FILE}"
required_dirs=(".codespaces" ".codespaces/scripts" ".codespaces/testing" ".codespaces/complete")
all_dirs_accessible=true

for dir in "${required_dirs[@]}"; do
    if [ -d "${dir}" ]; then
        echo "      \"${dir}\": \"accessible\"," >> "${REPORT_FILE}"
    else
        echo "      \"${dir}\": \"inaccessible\"," >> "${REPORT_FILE}"
        all_dirs_accessible=false
    fi
done

if [ "$all_dirs_accessible" = false ]; then
    echo "      \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "      \"error\": \"Some required directories are inaccessible\"" >> "${REPORT_FILE}"
    echo "    }," >> "${REPORT_FILE}"
    echo "  \"status\": \"failed\"," >> "${REPORT_FILE}"
    echo "  \"error\": \"File system verification failed\"" >> "${REPORT_FILE}"
    echo "}" >> "${REPORT_FILE}"
    exit 1
fi

echo "      \"status\": \"passed\"" >> "${REPORT_FILE}"
echo "    }" >> "${REPORT_FILE}"

# Complete report
echo "  }," >> "${REPORT_FILE}"
echo "  \"status\": \"passed\"," >> "${REPORT_FILE}"
echo "  \"message\": \"Environment setup verification completed successfully\"" >> "${REPORT_FILE}"
echo "}" >> "${REPORT_FILE}"

# Update checklist
sed -i 's/- \[ \] Codespaces environment initialization/- [x] Codespaces environment initialization/' .codespaces/testing/production_testing.md

# Move completed checklist to complete directory
if [ -f ".codespaces/testing/production_testing.md" ]; then
    cp ".codespaces/testing/production_testing.md" ".codespaces/complete/testing/production_testing.md"
fi

exit 0
