# ClaudeLens

[![CI/CD](https://github.com/sjafferali/claudelens/actions/workflows/main.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/sjafferali/claudelens/branch/main/graph/badge.svg)](https://codecov.io/gh/sjafferali/claudelens)
[![Security](https://github.com/sjafferali/claudelens/actions/workflows/security.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![MongoDB](https://img.shields.io/badge/mongodb-7.0+-green.svg)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

Archive, search, and visualize your Claude conversation history. Transform your scattered Claude conversations into a comprehensive, searchable analytics platform with advanced insights and cost tracking.

## 🎯 At a Glance

ClaudeLens transforms your Claude conversations into a powerful analytics dashboard with real-time insights, beautiful visualizations, and intelligent search capabilities. See your AI interactions like never before.

<div align="center">

### 📊 **Professional Analytics Dashboard**
![ClaudeLens Dashboard](./docs/images/dashboard-overview.png)
*Real-time dashboard with activity heatmaps, cost tracking, and session analytics*

### 💰 **Advanced Cost Analytics**
![Cost Analytics](./docs/images/analytics-dashboard.png)
*Comprehensive cost tracking with trend analysis, model breakdowns, and predictions*

### 🔍 **Intelligent Search Interface**
![Search Interface](./docs/images/search-interface.png)
*Advanced search with auto-suggestions, filtering, and highlighted results*

### 🌊 **Interactive Conversation Flow**
![Conversation Flow](./docs/images/sessions-interface.png)
*Interactive conversation flow visualization showing branching patterns and relationships*

</div>

## ✨ Features

### 🔍 **Advanced Search & Discovery**
- Full-text search across all conversations with highlighting
- Code-specific search with language filtering
- Search suggestions and autocomplete
- Recent search history for quick access

### 📊 **Comprehensive Analytics Dashboard**

Experience enterprise-grade analytics with ClaudeLens's sophisticated dashboard interface:

- **💰 Real-time Cost Tracking**: Interactive charts showing daily spending, model breakdowns, and cost predictions with confidence intervals
- **🎯 Token Efficiency Analytics**: Advanced percentile analysis (p50, p90, p95) with performance insights and usage patterns
- **🔧 Tool Execution Intelligence**: Detailed success rates, execution times, and error pattern analysis across all Claude tools
- **🌊 Interactive Conversation Flow**: ReactFlow-powered visualization showing conversation branching, sidechains, and dialogue complexity
- **📈 Performance Benchmarking**: Multi-dimensional comparisons across projects, teams, and time periods with actionable insights
- **🔥 GitHub-style Activity Heatmaps**: Visual timeline of your Claude usage patterns with timezone-aware daily/hourly breakdowns
- **🌿 Git Branch Analytics**: Development workflow insights showing Claude usage across different branches and project phases
- **💚 Session Health Monitoring**: Real-time error tracking, success rates, and conversation quality metrics
- **📁 Smart Directory Analysis**: Workspace organization insights with treemap visualizations and project structure analytics

<div align="center">

![Analytics Dashboard Features](./docs/images/analytics-dashboard.png)
*The analytics dashboard showcasing cost trends, activity heatmaps, and conversation flow diagrams*

</div>

### 🔄 **Intelligent Synchronization**
- Automatic sync from local Claude directory with file watching
- Multi-directory support for complex workflows
- Batch ingestion with deduplication and validation
- Support for Claude.ai, Claude Code CLI, and API conversations
- Real-time WebSocket updates for live synchronization

### 🎨 **Modern User Interface**

ClaudeLens features a polished, professional interface designed for power users:

- **🎯 Elegant Dashboard Design**: Clean sidebar navigation with sophisticated dark/light theme support and smooth transitions
- **📱 Responsive Excellence**: Mobile-friendly responsive design that works perfectly on desktop, tablet, and mobile devices
- **📊 Interactive Visualizations**: Rich charts powered by Recharts and ReactFlow with hover tooltips, zoom controls, and theme-aware styling
- **🔍 Smart Search Experience**: Auto-suggestions, advanced filtering with active badges, and highlighted search results
- **📈 Real-time Live Updates**: WebSocket-powered live statistics with animated value changes and connection status indicators
- **⚡ Performance Optimized**: Debounced search, lazy loading, optimized renders, and intelligent connection management
- **♿ Accessibility First**: ARIA labels, keyboard navigation, focus management, and screen reader support
- **🎨 Professional Polish**: Consistent typography, layered backgrounds, hover effects, and smooth loading states

<div align="center">

![UI Interface Showcase](./docs/images/projects-interface.png)
*ClaudeLens interface showing the clean navigation, interactive charts, and professional design system*

</div>

### 🛠️ **Developer Experience**
- Comprehensive REST API with OpenAPI documentation
- CLI tool for automation and integration
- Docker-based deployment with production-ready configuration
- Extensive test coverage (backend and frontend)
- Type-safe TypeScript implementation

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

The fastest way to get ClaudeLens running:

1. **Clone and configure**:
   ```bash
   git clone https://github.com/sjafferali/claudelens.git
   cd claudelens
   ```

2. **For production use**, edit `docker-compose.yml` and update:
   ```yaml
   environment:
     # REQUIRED: Use a strong password
     - MONGO_INITDB_ROOT_PASSWORD=your-very-secure-password-here

     # REQUIRED: Use a secure API key
     - API_KEY=your-secure-api-key-here

     # REQUIRED: Restrict CORS origins
     - BACKEND_CORS_ORIGINS=https://yourdomain.com
   ```

3. **Start the application**:
   ```bash
   docker compose up -d
   ```

4. **Access ClaudeLens** at http://localhost:3000

5. **Install and configure the CLI**:
   ```bash
   pip install claudelens-cli
   claudelens config set api_url http://localhost:8000
   claudelens config set api_key your-secure-api-key-here
   claudelens config add-claude-dir ~/.claude
   claudelens sync
   ```

### Option 2: Pre-built Docker Image

For custom deployments:

```bash
docker run -d \
  --name claudelens \
  -p 3000:8080 \
  -e MONGODB_URL="mongodb://user:pass@host:27017/claudelens" \
  -e API_KEY="your-secure-api-key" \
  sjafferali/claudelens:latest
```

### Option 3: Development Setup

For contributors and advanced users:

1. **Prerequisites**:
   - Docker and Docker Compose
   - Node.js 20+ for frontend development
   - Python 3.11+ with Poetry for backend development

2. **Quick development start**:
   ```bash
   git clone https://github.com/sjafferali/claudelens.git
   cd claudelens
   ./scripts/dev.sh --load-samples
   ```

3. **Individual components**:
   ```bash
   # Backend (port 8000)
   cd backend
   poetry install
   poetry run uvicorn app.main:app --reload

   # Frontend (port 5173)
   cd frontend
   npm install
   npm run dev

   # MongoDB (port 27017)
   docker compose -f docker/docker-compose.dev.yml up -d
   ```

## 🏗️ Architecture

ClaudeLens uses a modern multi-component architecture:

### **Components**
- **Frontend**: React 18 + TypeScript + Vite with TailwindCSS and comprehensive UI libraries
- **Backend**: FastAPI + Python 3.11 with MongoDB for high-performance API services
- **CLI Tool**: Python Click-based tool for automatic conversation synchronization
- **Database**: MongoDB 7.0 with full-text search and advanced indexing
- **Infrastructure**: Docker containerization with nginx reverse proxy

### **Technology Stack**

| Component | Technologies |
|-----------|-------------|
| **Frontend** | React, TypeScript, Vite, TailwindCSS, React Query, Zustand, Recharts, ReactFlow |
| **Backend** | FastAPI, Python 3.11, MongoDB, Motor, Pydantic, WebSockets, LiteLLM |
| **CLI** | Python 3.11, Click, Rich, Watchdog, HTTPX, Pydantic |
| **Infrastructure** | Docker, Docker Compose, Nginx, GitHub Actions |
| **Development** | Poetry, npm, ESLint, Ruff, Prettier, Pytest, Vitest, Pre-commit |

### **Data Flow**
1. **CLI tool** watches local Claude directory and syncs conversations to the FastAPI backend
2. **Backend** stores data in MongoDB with full-text indexing and analytics processing
3. **Frontend** queries the API for visualization, search, and analytics
4. **WebSocket connections** provide real-time updates across all components

## 📚 Documentation

### Quick Links
- **[UI/UX Guide](./docs/UI-GUIDE.md)** - Complete interface walkthrough with screenshots and features
- **[API Documentation](http://localhost:8000/docs)** - Interactive OpenAPI documentation
- **[CLI Reference](./docs/CLI.md)** - Command-line tool usage guide
- **[Configuration Guide](./docs/CONFIGURATION.md)** - Environment variables and deployment options
- **[Development Guide](#development)** - Contributing and development setup
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

### API Overview

ClaudeLens provides a comprehensive REST API with 67+ endpoints organized into these categories:

- **Analytics** (30 endpoints): Cost tracking, tool usage, session health, conversation flow analysis
- **Search** (5 endpoints): Full-text search with filtering and suggestions
- **Sessions** (5 endpoints): Session management with message threading
- **Messages** (7 endpoints): Message CRUD operations with context management
- **Projects** (6 endpoints): Project organization and statistics
- **Ingestion** (3 endpoints): Batch message ingestion with validation
- **WebSocket** (6 endpoints): Real-time updates for session and global statistics
- **Health/Status** (5 endpoints): System health monitoring and API status

<div align="center">

![API Documentation](./docs/images/dashboard-overview.png)
*Interactive OpenAPI documentation with comprehensive endpoint reference*

</div>

### Key Features by Endpoint Category

#### Analytics Endpoints
- **Cost Analytics**: `/api/v1/analytics/costs` - Cost tracking over time
- **Token Analytics**: `/api/v1/analytics/tokens` - Token usage and efficiency metrics
- **Tool Usage**: `/api/v1/analytics/tools/detailed` - Comprehensive tool execution analytics
- **Conversation Flow**: `/api/v1/analytics/conversation-flow` - Interactive flow visualization
- **Performance Benchmarks**: `/api/v1/analytics/benchmarks` - Multi-dimensional comparisons
- **Git Branch Analytics**: `/api/v1/analytics/git-branches` - Development workflow insights
- **Session Health**: `/api/v1/analytics/session/health` - Error tracking and success rates
- **Directory Usage**: `/api/v1/analytics/directory-usage` - Workspace organization analysis

#### Search & Discovery
- **Full-text Search**: `/api/v1/search/` - Advanced search with highlighting
- **Code Search**: `/api/v1/search/code` - Language-specific code search
- **Search Suggestions**: `/api/v1/search/suggestions` - Autocomplete functionality

#### Real-time Features
- **Session Updates**: `/ws/session/{session_id}` - Live session monitoring
- **Global Stats**: `/ws/stats` - Real-time analytics updates
- **Live Statistics**: `/ws/stats/live` - Current system statistics

## CLI Reference

The ClaudeLens CLI provides powerful automation for conversation synchronization:

### Installation
```bash
pip install claudelens-cli
```

### Configuration
```bash
# Set API connection details
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key

# Add Claude directories to sync
claudelens config add-claude-dir ~/.claude
claudelens config add-claude-dir /path/to/project/.claude

# View current configuration
claudelens config show
```

### Synchronization Commands
```bash
# Basic sync
claudelens sync

# Continuous monitoring (recommended)
claudelens sync --watch

# Project-specific sync
claudelens sync --project /path/to/specific/project

# Debug mode with dry run
claudelens sync --debug --dry-run

# Force re-sync (resolves duplicates)
claudelens sync --force --overwrite
```

### Monitoring and Status
```bash
# Check sync status
claudelens status

# Detailed status with statistics
claudelens status --detailed

# Version information
claudelens version
```

### Typical Workflows

**First-time Setup**:
```bash
claudelens config set api_url http://localhost:8000
claudelens config set api_key your-api-key
claudelens config add-claude-dir ~/.claude
claudelens sync --dry-run  # Test configuration
claudelens sync            # Initial sync
```

**Daily Usage**:
```bash
claudelens status          # Check current state
claudelens sync --watch    # Start continuous sync
```

**Troubleshooting**:
```bash
claudelens status --detailed
claudelens sync --debug --dry-run
claudelens config show
claudelens sync --force
```

## Configuration

### Environment Variables

ClaudeLens uses environment variables for configuration. Here are the key variables:

#### Required Variables
```bash
# MongoDB connection (REQUIRED)
MONGODB_URL=mongodb://admin:password@localhost:27017/claudelens?authSource=admin

# Database name
DATABASE_NAME=claudelens

# API security (REQUIRED for production)
API_KEY=your-secure-api-key-here
```

#### Optional Variables
```bash
# Application settings
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Security settings
BACKEND_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Database tuning
MAX_CONNECTIONS_COUNT=100
MIN_CONNECTIONS_COUNT=10

# Environment
ENVIRONMENT=production
```

#### CLI Configuration
```bash
# CLI tool settings
CLAUDELENS_API_URL=http://localhost:8000
CLAUDELENS_API_KEY=your-api-key
CLAUDE_DIRS=/path/to/claude1,/path/to/claude2
```

### Production Deployment Checklist

**Security Requirements**:
- [ ] Change `MONGO_INITDB_ROOT_PASSWORD` from default
- [ ] Update `API_KEY` with a secure random key
- [ ] Restrict `BACKEND_CORS_ORIGINS` to your domain
- [ ] Use dedicated MongoDB user (not root)
- [ ] Enable MongoDB authentication
- [ ] Configure HTTPS with proper certificates

**Performance Optimization**:
- [ ] Adjust `MAX_CONNECTIONS_COUNT` based on load
- [ ] Configure nginx caching for static assets
- [ ] Set appropriate MongoDB connection pool sizes
- [ ] Monitor and tune uvicorn worker count
- [ ] Consider MongoDB replica sets for high availability

## Development

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ and npm
- Python 3.11+ and Poetry
- MongoDB 7.0+ (via Docker or standalone)

### Quick Development Setup
```bash
git clone https://github.com/sjafferali/claudelens.git
cd claudelens
./scripts/dev.sh --load-samples
```

### Individual Component Development

**Backend Development**:
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Development**:
```bash
cd frontend
npm install
npm run dev  # Starts on port 5173
```

**CLI Development**:
```bash
cd cli
poetry install
poetry run claudelens --help
```

**Database (Development)**:
```bash
docker compose -f docker/docker-compose.dev.yml up -d
# MongoDB on port 27017, Mongo Express on port 8081
```

### Testing

**Backend Tests**:
```bash
cd backend
poetry run pytest --cov=app --cov-report=xml --cov-report=term
```

**Frontend Tests**:
```bash
cd frontend
npm test              # Interactive mode
npm run test:coverage # Coverage report
npm run test:ci       # CI mode
```

**CLI Tests**:
```bash
cd cli
poetry run pytest --cov=claudelens_cli
```

### Code Quality Tools
```bash
# Run all CI checks locally
./scripts/run_ci_checks.sh

# Quick checks with auto-fix
./scripts/run_ci_checks.sh --quick --auto-fix

# Individual tools
npm run lint && npm run format     # Frontend
poetry run ruff check && poetry run black .  # Backend
```

### Development Scripts

- **`./scripts/dev.sh`**: Complete development environment setup
  - `--persistent-db`: Keep database running between sessions
  - `--load-samples`: Generate sample data for testing
  - `--backend-only`: Start only backend services
  - `--frontend-only`: Start only frontend services

- **`./scripts/build.sh`**: Build production Docker image
- **`./scripts/run_ci_checks.sh`**: Run comprehensive CI checks locally

## Troubleshooting

### Common Issues

**CLI Sync Fails**:
```bash
# Check configuration
claudelens config show

# Verify backend is running
curl http://localhost:8000/api/v1/health

# Debug sync process
claudelens sync --debug --dry-run
```

**No Conversations Found**:
```bash
# Verify Claude directory path
ls ~/.claude

# Add correct directory
claudelens config add-claude-dir /correct/path/to/.claude
```

**Docker Services Won't Start**:
```bash
# Check port conflicts
docker ps
netstat -tulpn | grep :27017

# View service logs
docker compose logs claudelens
docker compose logs mongodb
```

**Database Connection Issues**:
```bash
# Check MongoDB status
docker compose ps

# Test connection string
mongosh "mongodb://admin:password@localhost:27017/claudelens?authSource=admin"

# Verify environment variables
docker compose exec claudelens env | grep MONGODB
```

**Frontend Development Issues**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Check Node.js version (requires 20+)
node --version
```

### Performance Issues

**Slow Search**:
- Verify MongoDB text indexes are created
- Check `scripts/update_text_index.py` for index management
- Monitor MongoDB performance with Mongo Express

**High Memory Usage**:
- Adjust MongoDB connection pool settings
- Monitor Docker container resource usage
- Consider increasing Docker memory limits

**Sync Performance**:
- Use `--watch` mode for continuous sync instead of frequent manual syncs
- Check Claude directory size and consider splitting large projects
- Monitor CLI debug output for bottlenecks

## 🌟 Why Choose ClaudeLens?

### **Enterprise-Ready Analytics**
ClaudeLens isn't just another conversation viewer—it's a comprehensive analytics platform that provides the insights you need to optimize your AI workflow. With **67+ API endpoints**, **real-time WebSocket updates**, and **advanced visualization capabilities**, it's built for users who demand professional-grade tools.

### **Beautiful, Intuitive Interface**
Our sophisticated **React + TypeScript** interface provides a smooth, responsive experience with:
- **Professional dark/light themes** with smooth transitions
- **Interactive charts and graphs** powered by Recharts and ReactFlow
- **Real-time updates** with WebSocket integration and animated statistics
- **Mobile-responsive design** that works perfectly on all devices

<div align="center">

![Feature Showcase](./docs/images/analytics-dashboard.png)

</div>

### **Comprehensive Documentation**
Every feature is thoroughly documented with:
- **Step-by-step setup guides** for multiple deployment scenarios
- **Complete API reference** with interactive examples
- **Detailed UI walkthrough** in our [UI/UX Guide](./docs/UI-GUIDE.md)
- **Production deployment guides** with security best practices

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `./scripts/run_ci_checks.sh`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to your branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style
- **Backend**: Follows PEP 8 with Ruff linting and Black formatting
- **Frontend**: Uses ESLint and Prettier with TypeScript strict mode
- **Commits**: Use imperative mood (e.g., "Add feature" not "Added feature")

## License

MIT License - see [LICENSE](./LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/sjafferali/claudelens/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sjafferali/claudelens/discussions)
- **Documentation**: [docs/](./docs/) directory
- **API Reference**: http://localhost:8000/docs (when running)

---

**ClaudeLens** - Transform your Claude conversations into actionable insights. Built with ❤️ using modern technologies and best practices.
