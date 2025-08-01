# Task 02: Development Environment Setup

## Status
**Status:** TODO  
**Priority:** High  
**Estimated Time:** 1.5 hours

## Purpose
Set up the complete development environment with all necessary dependencies, development tools, and configurations for Python, Node.js, and Docker environments.

## Current State
- Basic project structure exists
- Poetry and npm projects initialized
- No dependencies installed

## Target State
- All development dependencies installed
- Linting and formatting tools configured
- Testing frameworks set up
- Pre-commit hooks configured
- Docker development environment ready

## Implementation Details

### 1. Backend Python Dependencies

**Update `backend/pyproject.toml`:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
motor = "^3.3.0"
pydantic = "^2.4.0"
pydantic-settings = "^2.0.0"
python-multipart = "^0.0.6"
httpx = "^0.25.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
redis = "^5.0.0"
aiofiles = "^23.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
pytest-xdist = "^3.3.0"
testcontainers = {extras = ["mongodb", "redis"], version = "^3.7.0"}
ruff = "^0.1.0"
mypy = "^1.6.0"
black = "^23.10.0"
isort = "^5.12.0"
pre-commit = "^3.5.0"
```

Install dependencies:
```bash
cd backend
poetry install
```

### 2. Frontend Dependencies

**Update `frontend/package.json`:**
```json
{
  "devDependencies": {
    "@types/node": "^20.8.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.7.0",
    "@typescript-eslint/parser": "^6.7.0",
    "@vitejs/plugin-react": "^4.1.0",
    "eslint": "^8.50.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "prettier": "^3.0.3",
    "typescript": "^5.2.0",
    "vite": "^4.5.0",
    "vitest": "^0.34.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "axios": "^1.5.0",
    "recharts": "^2.8.0",
    "date-fns": "^2.30.0",
    "clsx": "^2.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "@radix-ui/react-dropdown-menu": "^2.0.0",
    "@radix-ui/react-tabs": "^1.0.0",
    "react-syntax-highlighter": "^15.5.0",
    "@types/react-syntax-highlighter": "^15.5.0"
  }
}
```

Install dependencies:
```bash
cd frontend
npm install
```

### 3. CLI Tool Dependencies

**Update `cli/pyproject.toml`:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.0"
httpx = "^0.25.0"
rich = "^13.6.0"
watchdog = "^3.0.0"
pydantic = "^2.4.0"
aiofiles = "^23.2.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
ruff = "^0.1.0"
mypy = "^1.6.0"
```

Install dependencies:
```bash
cd cli
poetry install
```

### 4. Configure Linting Tools

**Backend `.ruff.toml`:**
```toml
line-length = 88
select = ["E", "F", "B", "I", "N", "UP", "YTT", "ASYNC", "S", "A", "C4", "DTZ", "ICN", "PIE", "PT", "RSE", "RET", "SIM", "TID", "TCH", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["E501", "B008", "B904"]
target-version = "py311"

[per-file-ignores]
"tests/*" = ["S101", "PLR2004"]
```

**Frontend `.eslintrc.json`:**
```json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "plugins": ["react-refresh"],
  "rules": {
    "react-refresh/only-export-components": [
      "warn",
      { "allowConstantExport": true }
    ]
  }
}
```

**`.prettierrc`:**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### 5. Configure Testing

**Backend `pytest.ini`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
```

**Frontend `vite.config.ts`:**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

### 6. Pre-commit Configuration

**`.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
        files: ^(backend|cli)/

  - repo: https://github.com/psf/black
    rev: 23.10.0
    hooks:
      - id: black
        files: ^(backend|cli)/

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.3
    hooks:
      - id: prettier
        files: ^frontend/
        types_or: [javascript, jsx, ts, tsx, css, json]
```

Install pre-commit:
```bash
pip install pre-commit
pre-commit install
```

### 7. TypeScript Configuration

**Frontend `tsconfig.json`:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 8. Tailwind CSS Setup

**Frontend `tailwind.config.js`:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

**Frontend `postcss.config.js`:**
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

**Frontend `src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### 9. Environment Configuration

**`.env.example`:**
```env
# Backend
MONGODB_URL=mongodb://localhost:27017/claudelens
REDIS_URL=redis://localhost:6379
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret

# Frontend
VITE_API_URL=http://localhost:8000

# CLI
CLAUDELENS_API_URL=http://localhost:8000
CLAUDELENS_API_KEY=your-api-key-here
```

### 10. PyCharm Configuration

**PyCharm Settings:**
- Enable Ruff as external tool for Python linting
- Configure Black as the Python formatter
- Set up Prettier for JavaScript/TypeScript formatting
- Configure ESLint integration for frontend code
- Enable EditorConfig support (built-in)

**Note:** PyCharm automatically detects most project settings from configuration files like `.editorconfig`, `pyproject.toml`, `.eslintrc.json`, and `.prettierrc`.

## Required Technologies
- Poetry (Python package manager)
- npm (Node package manager)
- Python 3.11+
- Node.js 20+

## Success Criteria
- [ ] All backend dependencies installed via Poetry
- [ ] All frontend dependencies installed via npm
- [ ] All CLI dependencies installed via Poetry
- [ ] Linting tools configured (Ruff, ESLint, Prettier)
- [ ] Testing frameworks configured
- [ ] Pre-commit hooks installed and working
- [ ] TypeScript configuration complete
- [ ] Tailwind CSS configured
- [ ] Environment variables documented

## Notes
- Use `poetry install` and `npm install` to install dependencies
- Run `pre-commit install` to set up git hooks
- All tools should work with PyCharm out of the box
- Keep development dependencies separate from production