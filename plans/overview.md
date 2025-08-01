# ClaudeLens Overview

## What is ClaudeLens?

ClaudeLens is a comprehensive archive and visualization tool for Claude conversations. It transforms your scattered Claude conversation history into a searchable, analyzable, and visual archive. The application supports conversations from Claude.ai, Claude Code CLI, and Claude API interactions.

## Key Features

### 1. Conversation Archive
- **Automatic Syncing**: CLI tool monitors your local Claude directory and syncs new conversations
- **Full History**: Preserves complete conversation threads including tool uses, costs, and metadata
- **Multi-Project Support**: Organizes conversations by project/workspace
- **Deduplication**: Intelligent detection prevents duplicate conversation uploads

### 2. Search & Discovery
- **Full-Text Search**: Search across all message content with relevance ranking
- **Advanced Filters**: Filter by date, project, model, cost, message type
- **Code Search**: Specialized search for code blocks with syntax awareness
- **Search History**: Save and reuse common searches

### 3. Visualization & Analytics
- **Activity Heatmap**: Visualize usage patterns over time
- **Cost Analytics**: Track spending by model, project, and time period
- **Token Usage**: Monitor token consumption trends
- **Model Usage**: See which Claude models you use most
- **Response Time Analysis**: Track model response times

### 4. Conversation Viewer
- **Thread View**: Navigate conversation threads with parent-child relationships
- **Syntax Highlighting**: Beautiful code rendering with language detection
- **Tool Use Visualization**: Clear display of tool calls and results
- **Export Options**: Export conversations in Markdown, JSON, or PDF

### 5. Project Management
- **Project Dashboard**: Overview of all your Claude projects
- **Project Stats**: Conversations, costs, and usage per project
- **Project Comparison**: Compare activity across projects

## User Interfaces

### Web Application
- **Modern SPA**: React-based single-page application
- **Responsive Design**: Works on desktop and mobile devices
- **Dark/Light Themes**: Comfortable viewing in any environment
- **Real-time Updates**: Live updates when new conversations are synced

### REST API
- **RESTful Design**: Standard HTTP methods and status codes
- **Authentication**: API key-based authentication
- **Rate Limiting**: Configurable rate limits
- **OpenAPI Spec**: Full API documentation with Swagger UI

### CLI Tool
- **Simple Commands**: `claudelens sync`, `claudelens status`, `claudelens config`
- **Watch Mode**: Continuous monitoring for new conversations
- **Progress Tracking**: Clear feedback during sync operations
- **Configuration**: Easy setup with config file or environment variables

## Technology Stack

### Backend (Python)
- **FastAPI**: Modern, fast web framework with automatic OpenAPI docs
- **Motor**: Async MongoDB driver for Python
- **Pydantic**: Data validation and settings management
- **pytest**: Testing framework with async support
- **Ruff**: Fast Python linter and formatter
- **Poetry**: Dependency management and packaging

### Frontend (TypeScript/React)
- **React 18**: Latest React with concurrent features
- **Vite**: Lightning-fast build tool and dev server
- **TanStack Query**: Powerful data fetching and caching
- **Zustand**: Lightweight state management
- **Recharts**: Composable charting library
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives

### Database
- **MongoDB**: Document database perfect for JSON conversation data
- **Indexes**: Optimized for search, timestamp queries, and aggregations
- **GridFS**: For storing large conversation exports

### Infrastructure
- **Docker**: Single container with both frontend and backend
- **Docker Compose**: Easy deployment with MongoDB
- **GitHub Actions**: CI/CD pipeline for testing and building
- **Testcontainers**: Integration testing with real MongoDB

## Data Flow

1. **Local Claude Directory** → **CLI Tool** → **Backend API** → **MongoDB**
2. **MongoDB** → **Backend API** → **Frontend** → **User**
3. **User Search** → **Frontend** → **API** → **MongoDB Full-Text Search**

## Security & Privacy

- **Local First**: All data stays on your infrastructure
- **No External Services**: No data sent to third parties
- **API Authentication**: Secure API key management
- **Input Validation**: Comprehensive validation to prevent injection
- **Rate Limiting**: Protection against abuse

## Performance Targets

- **Search Response**: < 100ms for most queries
- **Page Load**: < 1s initial load, < 200ms navigation
- **Sync Speed**: 1000+ messages/second ingestion
- **Concurrent Users**: Support 100+ concurrent web users
- **Database Size**: Efficient with 1M+ messages

## Future Enhancements

- **Claude API Integration**: Direct API usage tracking
- **Team Features**: Shared conversation libraries
- **AI Insights**: ML-powered conversation analysis
- **Plugins**: Extensible architecture for custom features
- **Mobile Apps**: Native iOS/Android applications