#!/bin/bash
set -e

# Run CI checks locally - mimics GitHub Actions workflows
# This script runs all tests, linters, and checks that run in CI

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
EXIT_CODE=0
AUTO_FIXES_APPLIED=()

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# CI tools virtual environment
CI_VENV="$PROJECT_ROOT/.ci-venv"

# Helper functions
print_section() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

run_check() {
    local name=$1
    local command=$2
    
    echo -e "${YELLOW}Running: $name${NC}"
    if eval "$command"; then
        print_success "$name passed"
    else
        print_error "$name failed"
        EXIT_CODE=1
        return 1
    fi
    return 0
}

# Auto-fix functions
auto_fix_prettier() {
    if [ "$AUTO_FIX" = true ]; then
        echo -e "${YELLOW}Auto-fixing Prettier formatting...${NC}"
        local current_dir=$(pwd)
        cd "$PROJECT_ROOT/frontend"
        npm run format
        print_success "Prettier formatting fixed"
        AUTO_FIXES_APPLIED+=("Prettier formatting")
        cd "$current_dir"
    fi
}

auto_fix_eslint() {
    if [ "$AUTO_FIX" = true ]; then
        echo -e "${YELLOW}Auto-fixing ESLint issues...${NC}"
        local current_dir=$(pwd)
        cd "$PROJECT_ROOT/frontend"
        npm run lint -- --fix
        print_success "ESLint issues fixed (where possible)"
        AUTO_FIXES_APPLIED+=("ESLint")
        cd "$current_dir"
    fi
}

auto_fix_ruff() {
    if [ "$AUTO_FIX" = true ]; then
        echo -e "${YELLOW}Auto-fixing Ruff issues...${NC}"
        local path=$1
        local name=$(basename "$path")
        local current_dir=$(pwd)
        cd "$path"
        "$CI_VENV/bin/ruff" check . --fix --select E,F,I --ignore E501
        print_success "Ruff issues fixed (where possible)"
        AUTO_FIXES_APPLIED+=("Ruff ($name)")
        cd "$current_dir"
    fi
}

# Parse arguments
SKIP_TESTS=false
SKIP_LINT=false
SKIP_SECURITY=false
SKIP_DOCKER=true  # Skip Docker build by default
QUICK=false
AUTO_FIX=true  # Auto-fix is enabled by default

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-tests)
      SKIP_TESTS=true
      shift
      ;;
    --skip-lint)
      SKIP_LINT=true
      shift
      ;;
    --skip-security)
      SKIP_SECURITY=true
      shift
      ;;
    --skip-docker)
      SKIP_DOCKER=true
      shift
      ;;
    --quick)
      QUICK=true
      shift
      ;;
    --include-docker)
      SKIP_DOCKER=false
      shift
      ;;
    --auto-fix)
      AUTO_FIX=true
      shift
      ;;
    --no-auto-fix)
      AUTO_FIX=false
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --skip-tests      Skip running tests"
      echo "  --skip-lint       Skip linting checks"
      echo "  --skip-security   Skip security scans"
      echo "  --skip-docker     Skip Docker build test (default: true)"
      echo "  --include-docker  Include Docker build test"
      echo "  --quick           Run quick tests only (similar to PR checks)"
      echo "  --auto-fix        Automatically fix common issues (default: enabled)"
      echo "  --no-auto-fix     Disable automatic fixes"
      echo "  -h, --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Main script
print_section "ClaudeLens CI Checks"
echo "This script runs all CI checks locally"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check prerequisites
print_section "Checking Prerequisites"

# Change to project root
cd "$PROJECT_ROOT"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
else
    print_success "Python $(python3 --version | cut -d' ' -f2) found"
fi

# Check Poetry
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install it: https://python-poetry.org/docs/#installation"
    exit 1
else
    print_success "Poetry $(poetry --version | cut -d' ' -f3) found"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
else
    print_success "Node.js $(node --version) found"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed"
    exit 1
else
    print_success "npm $(npm --version) found"
fi

# Setup CI virtual environment for tools
if [ ! -d "$CI_VENV" ]; then
    echo -e "\n${YELLOW}Creating CI tools virtual environment...${NC}"
    python3 -m venv "$CI_VENV"
fi

# Activate virtual environment
source "$CI_VENV/bin/activate"

# Upgrade pip in virtual environment
echo -e "${YELLOW}Ensuring pip is up to date...${NC}"
python -m pip install --upgrade pip --quiet

# Python Tests
if [ "$SKIP_TESTS" = false ]; then
    print_section "Python Tests"
    
    # Backend tests
    echo -e "\n${YELLOW}Backend Tests${NC}"
    cd "$PROJECT_ROOT/backend"
    if [ ! -d ".venv" ]; then
        echo "Installing backend dependencies..."
        poetry install --with dev
    fi
    
    if [ "$QUICK" = true ]; then
        run_check "Backend quick tests" "poetry run pytest -x --ff"
    else
        run_check "Backend tests with coverage" "poetry run pytest --cov=app --cov-report=xml --cov-report=term"
    fi
    cd "$PROJECT_ROOT"
    
    # CLI tests
    echo -e "\n${YELLOW}CLI Tests${NC}"
    cd "$PROJECT_ROOT/cli"
    if [ ! -d ".venv" ]; then
        echo "Installing CLI dependencies..."
        poetry install --with dev
    fi
    
    if [ "$QUICK" = true ]; then
        run_check "CLI quick tests" "poetry run pytest -x --ff"
    else
        run_check "CLI tests with coverage" "poetry run pytest --cov=claudelens_cli --cov-report=xml --cov-report=term"
    fi
    cd "$PROJECT_ROOT"
fi

# Frontend Tests
if [ "$SKIP_TESTS" = false ]; then
    print_section "Frontend Tests"
    
    cd "$PROJECT_ROOT/frontend"
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm ci
    fi
    
    if [ "$QUICK" = true ]; then
        run_check "Frontend tests" "npm test -- --run --pool=threads --poolOptions.threads.maxThreads=2"
    else
        run_check "Frontend tests with coverage" "npm run test:coverage"
    fi
    cd "$PROJECT_ROOT"
fi

# Python Linting
if [ "$SKIP_LINT" = false ]; then
    print_section "Python Linting"
    
    # Install linting tools in CI virtual environment
    echo "Installing linting tools..."
    python -m pip install --quiet ruff mypy
    
    # Ruff checks
    echo -e "\n${YELLOW}Ruff Linting${NC}"
    if ! run_check "Backend ruff" "cd \"$PROJECT_ROOT/backend\" && \"$CI_VENV/bin/ruff\" check . --select E,F,I --ignore E501"; then
        auto_fix_ruff "$PROJECT_ROOT/backend"
        if [ "$AUTO_FIX" = true ]; then
            # Re-run the check after fix
            run_check "Backend ruff (after fix)" "cd \"$PROJECT_ROOT/backend\" && \"$CI_VENV/bin/ruff\" check . --select E,F,I --ignore E501"
        fi
    fi
    
    if ! run_check "CLI ruff" "cd \"$PROJECT_ROOT/cli\" && \"$CI_VENV/bin/ruff\" check . --select E,F,I --ignore E501"; then
        auto_fix_ruff "$PROJECT_ROOT/cli"
        if [ "$AUTO_FIX" = true ]; then
            # Re-run the check after fix
            run_check "CLI ruff (after fix)" "cd \"$PROJECT_ROOT/cli\" && \"$CI_VENV/bin/ruff\" check . --select E,F,I --ignore E501"
        fi
    fi
    
    # MyPy checks (only if not quick mode)
    if [ "$QUICK" = false ]; then
        echo -e "\n${YELLOW}MyPy Type Checking${NC}"
        
        cd "$PROJECT_ROOT/backend"
        if [ ! -d ".venv" ]; then
            poetry install --with dev
        fi
        run_check "Backend mypy" "poetry run mypy app/ --ignore-missing-imports --allow-untyped-defs --allow-untyped-calls"
        cd "$PROJECT_ROOT"
        
        cd "$PROJECT_ROOT/cli"
        if [ ! -d ".venv" ]; then
            poetry install --with dev
        fi
        run_check "CLI mypy" "poetry run mypy claudelens_cli/ --ignore-missing-imports --allow-untyped-defs --allow-untyped-calls"
        cd "$PROJECT_ROOT"
    fi
fi

# Frontend Linting
if [ "$SKIP_LINT" = false ]; then
    print_section "Frontend Linting"
    
    cd "$PROJECT_ROOT/frontend"
    if [ ! -d "node_modules" ]; then
        npm ci
    fi
    
    if ! run_check "ESLint" "npm run lint"; then
        auto_fix_eslint
        if [ "$AUTO_FIX" = true ]; then
            # Re-run the check after fix
            run_check "ESLint (after fix)" "npm run lint"
        fi
    fi
    
    if ! run_check "Prettier formatting check" "npm run format:check"; then
        auto_fix_prettier
        if [ "$AUTO_FIX" = true ]; then
            # Re-run the check after fix
            run_check "Prettier formatting check (after fix)" "npm run format:check"
        fi
    fi
    
    if [ "$QUICK" = false ]; then
        run_check "TypeScript check" "npm run type-check"
    fi
    cd "$PROJECT_ROOT"
fi

# Security Scanning
if [ "$SKIP_SECURITY" = false ]; then
    print_section "Security Scanning"
    
    # Trivy scan
    if command -v trivy &> /dev/null; then
        if [ "$QUICK" = true ]; then
            run_check "Trivy quick scan (CRITICAL only)" "cd \"$PROJECT_ROOT\" && trivy fs . --severity CRITICAL --exit-code 1"
        else
            run_check "Trivy full scan" "cd \"$PROJECT_ROOT\" && trivy fs . --severity CRITICAL,HIGH"
        fi
    else
        echo -e "${YELLOW}Trivy not installed. Skipping vulnerability scan.${NC}"
        echo "Install with: brew install trivy (macOS) or see https://github.com/aquasecurity/trivy"
    fi
    
    # Python dependency check (only if not quick mode)
    if [ "$QUICK" = false ]; then
        echo -e "\n${YELLOW}Python Dependency Security${NC}"
        python -m pip install --quiet pip-audit
        
        cd "$PROJECT_ROOT/backend"
        run_check "Backend pip-audit check" "\"$CI_VENV/bin/pip-audit\" || true"
        cd "$PROJECT_ROOT"
        
        cd "$PROJECT_ROOT/cli"
        run_check "CLI pip-audit check" "\"$CI_VENV/bin/pip-audit\" || true"
        cd "$PROJECT_ROOT"
    fi
    
    # npm audit (only if not quick mode)
    if [ "$QUICK" = false ]; then
        echo -e "\n${YELLOW}npm Dependency Audit${NC}"
        cd "$PROJECT_ROOT/frontend"
        run_check "npm audit" "npm audit --json > npm-audit.json && ([ ! -s npm-audit.json ] || (cat npm-audit.json | jq -e '.vulnerabilities | length == 0'))"
        rm -f npm-audit.json
        cd "$PROJECT_ROOT"
    fi
fi

# Docker Build Test (only if explicitly requested)
if [ "$SKIP_DOCKER" = false ]; then
    print_section "Docker Build Test"
    
    if command -v docker &> /dev/null; then
        run_check "Docker build" "cd \"$PROJECT_ROOT\" && docker build -f docker/Dockerfile -t claudelens:ci-test ."
        
        # Clean up
        docker rmi claudelens:ci-test 2>/dev/null || true
    else
        echo -e "${YELLOW}Docker not installed. Skipping Docker build test.${NC}"
    fi
fi

# Summary
print_section "CI Check Summary"

if [ $EXIT_CODE -eq 0 ]; then
    print_success "All CI checks passed! ✨"
else
    print_error "Some CI checks failed. Please fix the issues above."
    if [ "$AUTO_FIX" = false ]; then
        echo -e "${YELLOW}Tip: Auto-fix is disabled. Remove --no-auto-fix to automatically fix some issues${NC}"
    fi
fi

# Show auto-fixes summary
if [ ${#AUTO_FIXES_APPLIED[@]} -gt 0 ] && [ "$AUTO_FIX" = true ]; then
    echo -e "\n${YELLOW}Auto-fixes applied:${NC}"
    for fix in "${AUTO_FIXES_APPLIED[@]}"; do
        echo -e "  ${GREEN}✓${NC} $fix"
    done
    echo -e "\n${YELLOW}Please review the changes and commit if they look good.${NC}"
fi

# Deactivate virtual environment
deactivate 2>/dev/null || true

exit $EXIT_CODE