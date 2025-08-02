# ClaudeLens Development Tasks

This directory contains detailed prompts for AI agents to implement specific features in the ClaudeLens application.

## Available Tasks

### 1. [Session Search and Filtering](./session-search-filtering.md)
Implement a comprehensive search and filtering UI for the sessions page, including:
- Text search functionality
- Date range filtering
- Sort options
- Project filtering
- URL state management

**Priority**: High  
**Estimated Effort**: Medium  
**Dependencies**: None

### 2. [Conversation Pagination](./conversation-pagination.md)
Implement efficient pagination for long conversation threads, including:
- Virtual scrolling for performance
- Load more functionality
- Navigation aids (jump to top/bottom)
- Search within conversation
- Keyboard shortcuts

**Priority**: High  
**Estimated Effort**: High  
**Dependencies**: None

## How to Use These Prompts

1. **Read the Entire Prompt**: Each task prompt provides comprehensive context about the application, current state, and detailed requirements.

2. **Set Up Development Environment**:
   ```bash
   # Start the development environment
   cd /Users/sjafferali/github/personal/claudelens
   ./scripts/dev.sh --load-samples
   
   # Frontend will be available at http://localhost:5173
   # Backend API at http://localhost:8000
   ```

3. **Understand the Codebase Structure**:
   - Backend: `/backend` - FastAPI application
   - Frontend: `/frontend` - React + TypeScript + Vite
   - Scripts: `/scripts` - Development utilities

4. **Follow the Implementation Guidelines**: Each prompt includes specific technical requirements, UI/UX guidelines, and success criteria.

5. **Test Your Implementation**: Use the testing considerations section to ensure your implementation is robust.

## General Development Guidelines

### Frontend Stack
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- @tanstack/react-query for data fetching
- lucide-react for icons
- React Router for navigation

### Backend Stack
- FastAPI (Python 3.11+)
- MongoDB for data storage
- Pydantic for data validation
- Poetry for dependency management

### Code Style
- Follow existing patterns in the codebase
- Use TypeScript strictly in frontend
- Implement proper error handling
- Add loading and empty states
- Ensure responsive design
- Write clean, self-documenting code

### Testing
- Test with sample data (`--load-samples` flag)
- Verify both desktop and mobile layouts
- Check browser console for errors
- Test error scenarios
- Validate performance requirements

## Getting Help

If you need clarification on any task:
1. Review the existing code for patterns
2. Check the API documentation at http://localhost:8000/docs
3. Look at similar implementations in the codebase
4. The prompts are designed to be comprehensive, but use your judgment for implementation details