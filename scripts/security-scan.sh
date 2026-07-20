#!/usr/bin/env bash
###############################################################################
# SentinelAI Security Scanner
# Runs multiple security scanning tools and fails on critical/high findings
###############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXIT_CODE=0

echo "=============================================="
echo "  SentinelAI Security Scanner"
echo "=============================================="
echo ""

# ---------------------------------------------------------------------------
# 1. Python Dependency Vulnerabilities (pip-audit)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[1/4] Running pip-audit (Python dependency vulnerabilities)...${NC}"
if command -v pip-audit &> /dev/null; then
    cd "$PROJECT_ROOT/backend"
    if pip-audit -r requirements.txt --desc --fix --dry-run 2>&1; then
        echo -e "${GREEN}✓ pip-audit: No vulnerabilities found${NC}"
    else
        echo -e "${RED}✗ pip-audit: Vulnerabilities detected!${NC}"
        EXIT_CODE=1
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠ pip-audit not installed. Install with: pip install pip-audit${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# 2. Python Security Linting (bandit)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[2/4] Running bandit (Python security linting)...${NC}"
if command -v bandit &> /dev/null; then
    cd "$PROJECT_ROOT/backend"
    if bandit -r app/ -c pyproject.toml --severity-level high --confidence-level high -q 2>&1; then
        echo -e "${GREEN}✓ bandit: No high-severity issues found${NC}"
    else
        echo -e "${RED}✗ bandit: Security issues detected!${NC}"
        EXIT_CODE=1
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠ bandit not installed. Install with: pip install bandit${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# 3. Node.js Dependency Vulnerabilities (npm audit)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[3/4] Running npm audit (Node.js vulnerabilities)...${NC}"
if command -v npm &> /dev/null; then
    cd "$PROJECT_ROOT/frontend"
    if [ -f "package-lock.json" ]; then
        AUDIT_RESULT=$(npm audit --audit-level=high 2>&1) || true
        if echo "$AUDIT_RESULT" | grep -q "found 0 vulnerabilities"; then
            echo -e "${GREEN}✓ npm audit: No vulnerabilities found${NC}"
        elif echo "$AUDIT_RESULT" | grep -qi "high\|critical"; then
            echo -e "${RED}✗ npm audit: High/Critical vulnerabilities detected!${NC}"
            echo "$AUDIT_RESULT"
            EXIT_CODE=1
        else
            echo -e "${GREEN}✓ npm audit: No high/critical vulnerabilities${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No package-lock.json found in frontend/${NC}"
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠ npm not installed${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# 4. Trivy Filesystem Scan
# ---------------------------------------------------------------------------
echo -e "${YELLOW}[4/4] Running Trivy filesystem scan...${NC}"
if command -v trivy &> /dev/null; then
    cd "$PROJECT_ROOT"
    if trivy fs . --severity HIGH,CRITICAL --exit-code 1 --quiet 2>&1; then
        echo -e "${GREEN}✓ trivy: No high/critical vulnerabilities found${NC}"
    else
        echo -e "${RED}✗ trivy: Vulnerabilities detected!${NC}"
        EXIT_CODE=1
    fi
else
    echo -e "${YELLOW}⚠ trivy not installed. See: https://aquasecurity.github.io/trivy/${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "=============================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}  ✓ All security checks passed!${NC}"
else
    echo -e "${RED}  ✗ Security issues found! Fix before deploying.${NC}"
fi
echo "=============================================="

exit $EXIT_CODE
