# Task 04: GitHub Actions CI/CD Setup

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 2 hours

## Purpose
Set up comprehensive GitHub Actions workflows for continuous integration and deployment. This includes running tests, linters, security scans, and building Docker images for all components.

## Current State
- No CI/CD pipeline
- No automated testing
- No automated Docker builds

## Target State
- PR checks workflow running tests and linters
- Main branch workflow building and pushing Docker images
- Security scanning integrated
- Code coverage reporting
- Dependency vulnerability scanning

## Implementation Details

### 1. Main CI/CD Workflow

**`.github/workflows/main.yml`:**
```yaml
name: Main Branch CI/CD

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Backend Tests
  backend-tests:
    runs-on: ubuntu-latest
    name: Backend Tests
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: 1.6.1
        virtualenvs-create: true
        virtualenvs-in-project: true
        
    - name: Cache dependencies
      uses: actions/cache@v4
      with:
        path: |
          backend/.venv
          ~/.cache/pypoetry
        key: ${{ runner.os }}-poetry-${{ hashFiles('backend/poetry.lock') }}
        
    - name: Install dependencies
      run: |
        cd backend
        poetry install --with dev
        
    - name: Run tests with coverage
      run: |
        cd backend
        poetry run pytest --cov=app --cov-report=xml --cov-report=term
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage

  # CLI Tests
  cli-tests:
    runs-on: ubuntu-latest
    name: CLI Tests
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: 1.6.1
        virtualenvs-create: true
        virtualenvs-in-project: true
        
    - name: Cache dependencies
      uses: actions/cache@v4
      with:
        path: |
          cli/.venv
          ~/.cache/pypoetry
        key: ${{ runner.os }}-poetry-cli-${{ hashFiles('cli/poetry.lock') }}
        
    - name: Install dependencies
      run: |
        cd cli
        poetry install --with dev
        
    - name: Run tests with coverage
      run: |
        cd cli
        poetry run pytest --cov=claudelens_cli --cov-report=xml --cov-report=term
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        file: ./cli/coverage.xml
        flags: cli
        name: cli-coverage

  # Frontend Tests
  frontend-tests:
    runs-on: ubuntu-latest
    name: Frontend Tests
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run tests with coverage
      run: |
        cd frontend
        npm run test:coverage -- --reporter=junit --outputFile=test-results.xml
        
    - name: Upload test results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: frontend-test-results
        path: frontend/test-results.xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        file: ./frontend/coverage/lcov.info
        flags: frontend
        name: frontend-coverage

  # Linting - Python
  python-lint:
    runs-on: ubuntu-latest
    name: Python Linting
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Install Ruff
      run: pip install ruff mypy
        
    - name: Run Ruff on Backend
      run: |
        cd backend
        ruff check . --output-format=github
        
    - name: Run Ruff on CLI
      run: |
        cd cli
        ruff check . --output-format=github
        
    - name: Install Poetry for MyPy
      uses: snok/install-poetry@v1
      with:
        version: 1.6.1
        virtualenvs-create: true
        virtualenvs-in-project: true
        
    - name: Run MyPy on Backend
      run: |
        cd backend
        poetry install --with dev
        poetry run mypy app/ --ignore-missing-imports
        
    - name: Run MyPy on CLI
      run: |
        cd cli
        poetry install --with dev
        poetry run mypy claudelens_cli/ --ignore-missing-imports

  # Linting - Frontend
  frontend-lint:
    runs-on: ubuntu-latest
    name: Frontend Linting
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Run ESLint
      run: |
        cd frontend
        npm run lint
        
    - name: Check Prettier formatting
      run: |
        cd frontend
        npm run format:check
        
    - name: Run TypeScript check
      run: |
        cd frontend
        npm run type-check

  # Security Scanning
  security-scan:
    runs-on: ubuntu-latest
    name: Security Scanning
    permissions:
      security-events: write
      contents: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'
        
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

  # Dependency Security Check
  dependency-check:
    runs-on: ubuntu-latest
    name: Dependency Security Check
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Check Python dependencies
      run: |
        pip install safety
        cd backend && safety check || true
        cd ../cli && safety check || true
        
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        
    - name: Audit npm dependencies
      run: |
        cd frontend
        npm audit --json > npm-audit.json || true
        if [ -s npm-audit.json ]; then
          echo "::warning::npm audit found vulnerabilities"
          cat npm-audit.json | jq '.vulnerabilities'
        fi

  # Docker Build & Push
  docker-build:
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v'))
    runs-on: ubuntu-latest
    needs: [backend-tests, cli-tests, frontend-tests, python-lint, frontend-lint, security-scan]
    name: Docker Build & Push
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=tag
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=semver,pattern={{major}}
          type=sha,prefix={{branch}}-,format=short
          type=raw,value=latest,enable={{is_default_branch}}
        
    - name: Build and push Docker image
      uses: docker/build-push-action@v6
      with:
        context: .
        file: ./docker/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64
        
    - name: Generate SBOM
      uses: anchore/sbom-action@v0
      with:
        image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.version }}
        format: cyclonedx-json
        output-file: sbom.json
        
    - name: Upload SBOM
      uses: actions/upload-artifact@v4
      with:
        name: sbom
        path: sbom.json

  # Build CLI binaries
  build-cli:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ${{ matrix.os }}
    needs: [cli-tests, python-lint]
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.11']
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Install Poetry
      uses: snok/install-poetry@v1
      
    - name: Build CLI
      run: |
        cd cli
        poetry install
        poetry build
        
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: cli-${{ matrix.os }}
        path: cli/dist/*

  # All checks passed
  ci-success:
    runs-on: ubuntu-latest
    needs: [backend-tests, cli-tests, frontend-tests, python-lint, frontend-lint, security-scan, dependency-check]
    name: CI Success
    steps:
    - name: Success
      run: echo "All CI checks passed!"
```

### 2. Pull Request Workflow

**`.github/workflows/pr.yml`:**
```yaml
name: Pull Request Checks

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  # Quick tests for PRs
  quick-tests:
    name: Quick Tests
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install Poetry
      uses: snok/install-poetry@v1
      
    - name: Backend tests
      run: |
        cd backend
        poetry install --with dev
        poetry run pytest -x --ff
        
    - name: CLI tests
      run: |
        cd cli
        poetry install --with dev
        poetry run pytest -x --ff
        
    - name: Frontend tests
      run: |
        cd frontend
        npm ci
        npm test -- --watchAll=false --maxWorkers=2
  
  # Linting
  lint:
    name: Linting
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        
    - name: Python linting
      run: |
        pip install ruff
        cd backend && ruff check . --output-format=github
        cd ../cli && ruff check . --output-format=github
        
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Frontend linting
      run: |
        cd frontend
        npm ci
        npm run lint
        npm run format:check
  
  # Security quick scan
  security-quick:
    name: Security Quick Check
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        severity: 'CRITICAL'
        exit-code: '1'
        ignore-unfixed: true
  
  # Test Docker build
  docker-build-test:
    name: Test Docker Build
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
    - name: Test Docker build
      uses: docker/build-push-action@v6
      with:
        context: .
        file: ./docker/Dockerfile
        push: false
        tags: claudelens:test
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### 3. Security Workflow

**`.github/workflows/security.yml`:**
```yaml
name: Security Scanning

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    
    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript', 'python' ]
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
    
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
    
    - name: Autobuild
      uses: github/codeql-action/autobuild@v3
    
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Dependency Review
      uses: actions/dependency-review-action@v4
      with:
        fail-on-severity: high
```

### 4. Dependabot Configuration

**`.github/dependabot.yml`:**
```yaml
version: 2
updates:
  # Python dependencies - Backend
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    assignees:
      - "sjafferali"
    labels:
      - "dependencies"
      - "backend"
      
  # Python dependencies - CLI
  - package-ecosystem: "pip"
    directory: "/cli"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    assignees:
      - "sjafferali"
    labels:
      - "dependencies"
      - "cli"
      
  # JavaScript dependencies
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    assignees:
      - "sjafferali"
    labels:
      - "dependencies"
      - "frontend"
      
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    assignees:
      - "sjafferali"
    labels:
      - "dependencies"
      - "github-actions"
```

### 5. Auto-merge Dependabot PRs

**`.github/workflows/auto-merge-dependabot.yml`:**
```yaml
name: Auto-merge Dependabot PRs

on:
  pull_request:

permissions:
  contents: write
  pull-requests: write

jobs:
  dependabot:
    runs-on: ubuntu-latest
    if: ${{ github.actor == 'dependabot[bot]' }}
    
    steps:
    - name: Dependabot metadata
      id: metadata
      uses: dependabot/fetch-metadata@v2
      with:
        github-token: "${{ secrets.GITHUB_TOKEN }}"
        
    - name: Auto-merge minor and patch updates
      if: ${{ steps.metadata.outputs.update-type == 'version-update:semver-minor' || steps.metadata.outputs.update-type == 'version-update:semver-patch' }}
      run: gh pr merge --auto --merge "$PR_URL"
      env:
        PR_URL: ${{ github.event.pull_request.html_url }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 6. Update Frontend package.json Scripts

**Add to `frontend/package.json`:**
```json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui"
  }
}
```

### 7. Add Badges to README

**Update root `README.md`:**
```markdown
# ClaudeLens

[![CI/CD](https://github.com/sjafferali/claudelens/actions/workflows/main.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/sjafferali/claudelens/branch/main/graph/badge.svg)](https://codecov.io/gh/sjafferali/claudelens)
[![Security](https://github.com/sjafferali/claudelens/actions/workflows/security.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/security.yml)

Transform your Claude conversations into a searchable, visual archive.

...
```

## Required Technologies
- GitHub Actions
- Docker Buildx
- Codecov account (for coverage reporting)
- GitHub Container Registry

## Success Criteria
- [ ] Main workflow runs on push to main branch
- [ ] PR workflow runs on pull requests
- [ ] Security scanning configured and running
- [ ] Code coverage reporting to Codecov
- [ ] Docker images building and pushing to GHCR
- [ ] Dependabot configured for all ecosystems
- [ ] Auto-merge for minor dependency updates
- [ ] All workflows passing green

## Notes
- Use GitHub Container Registry (ghcr.io) for Docker images
- Enable branch protection rules after workflows are set up
- Configure Codecov integration for coverage badges
- Security scans should not block PRs but alert on issues
- Use matrix builds for multi-platform support