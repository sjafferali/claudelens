# Task 01: Project Setup and Initial Structure

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 2 hours

## Purpose
Initialize the ClaudeLens project with the proper directory structure, development environment configuration, and base tooling setup. This task establishes the foundation for all subsequent development work.

## Current State
- Project exists as `claudelens` directory
- Git repository already initialized with remote origin
- README.md and LICENSE files already created
- Plans directory with task specifications
- No application code structure yet

## Target State
- Complete project structure as defined in implementation plan
- All configuration files in place
- Development tools configured
- README.md expanded with full project information

## Implementation Details

### 1. Create Directory Structure
```bash
# Create all necessary directories
mkdir -p backend/{app/{api/routes,core,models,services},tests,scripts}
mkdir -p frontend/{src/{api,components,hooks,pages,store,types,utils},public,tests}
mkdir -p cli/{claudelens_cli/{commands,core,utils},tests}
mkdir -p docker scripts docs .github/workflows
```

### 2. Create Root Configuration Files

**`.gitignore`** (create new file)
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
dist/
build/
.npm
*.log
coverage/
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Project specific
.claudelens/
*.db
*.log
docker/data/
```

**`README.md`** (update existing file)
```markdown
# ClaudeLens

Archive, search, and visualize your Claude conversation history. Transform your scattered Claude conversations into a searchable, visual archive.

## Features
- 🔍 Full-text search across all conversations
- 📊 Usage analytics and cost tracking
- 🔄 Automatic sync from local Claude directory
- 🎨 Beautiful conversation viewer with syntax highlighting
- 📈 Activity heatmaps and insights
- 🏷️ Project-based organization
- 💾 Support for Claude.ai, Claude Code CLI, and API conversations

## Quick Start
[Installation and usage instructions - to be added]

## Components
- **Web Application**: React-based frontend for browsing and analyzing conversations
- **REST API**: FastAPI backend for data access and search
- **CLI Tool**: Automatic syncing from your local Claude directory

## Technology Stack
- Backend: Python, FastAPI, MongoDB
- Frontend: React, TypeScript, Vite
- Infrastructure: Docker, Docker Compose

## Documentation
See the [docs](./docs) directory for detailed documentation.

## License
MIT License - see [LICENSE](./LICENSE) file for details.
```

**`.editorconfig`**
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,js,ts,jsx,tsx}]
indent_style = space
indent_size = 4

[*.{json,yml,yaml,md}]
indent_style = space
indent_size = 2

[Makefile]
indent_style = tab
```

### 3. Create Development Scripts

**`scripts/dev.sh`**
```bash
#!/bin/bash
set -e

# Development environment setup script
echo "ClaudeLens Development Environment"
echo "=================================="

# Parse arguments
PERSISTENT_DB=false
LOAD_SAMPLES=false
BACKEND_ONLY=false
FRONTEND_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --persistent-db)
      PERSISTENT_DB=true
      shift
      ;;
    --load-samples)
      LOAD_SAMPLES=true
      shift
      ;;
    --backend-only)
      BACKEND_ONLY=true
      shift
      ;;
    --frontend-only)
      FRONTEND_ONLY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Implementation will be completed in later tasks
echo "Development script initialized. Implementation pending."
```

Make executable:
```bash
chmod +x scripts/dev.sh
```

### 4. Create Docker Configuration

**`docker/.dockerignore`**
```
**/__pycache__
**/*.pyc
**/node_modules
**/dist
**/build
**/.pytest_cache
**/.coverage
**/htmlcov
**/.env*
**/.git
**/venv
```

### 5. Initialize Backend (Python/Poetry)

```bash
cd backend
poetry init --name claudelens-backend --python "^3.11"
```

**`backend/pyproject.toml`** (base configuration)
```toml
[tool.poetry]
name = "claudelens-backend"
version = "0.1.0"
description = "ClaudeLens backend API"
authors = ["Your Name <email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.dev-dependencies]

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 88
select = ["E", "F", "B", "I"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 6. Initialize Frontend (Vite/React)

```bash
cd frontend
npm init -y
```

**`frontend/package.json`** (base configuration)
```json
{
  "name": "claudelens-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  }
}
```

### 7. Initialize CLI Tool

```bash
cd cli
poetry init --name claudelens-cli --python "^3.11"
```

### 8. Create Initial Documentation

**`docs/README.md`**
```markdown
# ClaudeLens Documentation

## Table of Contents
1. [Installation](./installation.md)
2. [Configuration](./configuration.md)
3. [API Reference](./api-reference.md)
4. [Development](./development.md)
5. [Deployment](./deployment.md)
```

## Required Technologies
- Python 3.11+
- Node.js 20+
- Poetry (Python package management)
- npm (Node package management)
- Docker & Docker Compose
- Git

## Success Criteria
- [ ] Complete directory structure created
- [ ] .gitignore file created
- [ ] .editorconfig file created
- [ ] README.md updated with full project information
- [ ] Backend Poetry project initialized
- [ ] Frontend npm project initialized
- [ ] CLI Poetry project initialized
- [ ] Development scripts created
- [ ] Docker configuration files created
- [ ] Initial documentation structure

## Notes
- This is the foundation task - all other tasks depend on this
- Ensure all directories are created even if empty
- Configuration files should be minimal but valid
- Don't install dependencies yet (handled in Task 02)