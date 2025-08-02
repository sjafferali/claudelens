# ClaudeLens

[![CI/CD](https://github.com/sjafferali/claudelens/actions/workflows/main.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/sjafferali/claudelens/branch/main/graph/badge.svg)](https://codecov.io/gh/sjafferali/claudelens)
[![Security](https://github.com/sjafferali/claudelens/actions/workflows/security.yml/badge.svg)](https://github.com/sjafferali/claudelens/actions/workflows/security.yml)

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

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/sjafferali/claudelens.git
cd claudelens
```

2. **For production use**, edit `docker-compose.yml` and update:
   - `SECRET_KEY` - Replace with a secure random key
   - `MONGO_INITDB_ROOT_PASSWORD` - Replace with a strong password
   - `BACKEND_CORS_ORIGINS` - Add your production domain

3. Start the application:
```bash
docker compose up -d
```

4. Access ClaudeLens at http://localhost:3000

The application includes:
- ClaudeLens web app (port 3000)
- MongoDB database (port 27017)
- Automatic database initialization

### Using Pre-built Docker Image

```bash
docker run -d \
  --name claudelens \
  -p 3000:8080 \
  -e MONGODB_URL="mongodb://user:pass@host:27017/claudelens" \
  -e SECRET_KEY="your-secret-key" \
  sjafferali/claudelens:latest
```

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