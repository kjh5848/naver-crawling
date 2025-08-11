# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack web application for scraping Naver blog content, featuring a FastAPI backend with React frontend. The system extracts blog posts (title, content, author, images) with a modern web interface for managing scraping jobs.

## Development Setup

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for Windows compatibility)
playwright install chromium
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Running the Application

#### Full Stack Development
```bash
# Run both frontend and backend with automatic port cleanup
python run_web.py

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

#### Individual Components
```bash
# Backend only (FastAPI)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend only (React/Vite)
cd frontend  
npm run dev
```

#### CLI Usage (Legacy)
```bash
# Direct scraping with standalone script
python standalone_scraper.py "https://blog.naver.com/blogId/postId" --headless
```

## Architecture Overview

### Full-Stack Architecture
```
Web Application (run_web.py)
├─> FastAPI Backend (backend/main.py)
│   ├─> Async Job Management: Background task processing
│   ├─> Process-Based Scraping: Windows-compatible subprocess execution
│   ├─> API Endpoints: REST API for scraping operations  
│   └─> Static File Serving: Backup UI hosting
├─> React Frontend (frontend/)
│   ├─> Vite Development Server: Hot reload + TypeScript
│   ├─> Modern UI: Tailwind CSS + Lucide icons
│   ├─> API Integration: Axios client with proxy configuration
│   └─> Real-time Updates: Job status polling
└─> Standalone Scraper (standalone_scraper.py)
    └─> Independent Process: Isolated Playwright execution
```

### Backend Architecture (FastAPI)
```
main.py: API server with async job management
├─> /scrape: POST - Start background scraping job
├─> /job/{id}: GET - Check job status and progress  
├─> /jobs: GET - List all active jobs
├─> /download/{id}: GET - Download results in JSON/CSV
├─> /stats: GET - Overall scraping statistics
└─> Background Tasks: Process-based scraping execution
```

### Core Scraping Components (src/)
```
NaverBlogScraper (main_scraper.py) 
├─> URLParser: Validates and normalizes Naver blog URLs
├─> SyncNaverBlogScraper: Playwright sync API for Windows compatibility
├─> ImageDownloader: Downloads and optimizes images locally
├─> DataStorage: Saves data to SQLite/JSON/Markdown
└─> Utils: RateLimiter + RetryHandler for robust scraping
```

### Critical Implementation Details

**Windows Compatibility**: Uses process-based scraping to avoid `asyncio.create_subprocess_exec` limitations on Windows. The `standalone_scraper.py` script runs in separate processes spawned by the FastAPI backend.

**Playwright Integration**: Migrated from Selenium to Playwright for better performance and reliability. Uses sync API in `backend/scraper_sync.py` to avoid Windows async subprocess issues.

**Iframe Handling**: Naver blogs use iframe containers. The scraper automatically detects and switches to `mainFrame` iframe before content extraction using Playwright's frame handling.

**CSS Selector Strategy**: Multiple fallback selectors for different Naver blog versions:
- Smart Editor 3.0: `.se-title-text`, `div.se-main-container`
- Legacy versions: `.pcol1`, `div#postViewArea`  
- Smart Editor 2.0: `div.se_title`, `div.se_component_wrap`

**Job Management**: FastAPI manages scraping jobs with unique UUIDs, progress tracking, and result storage. Jobs run in background tasks with real-time status updates.

**Port Configuration**: 
- Frontend: http://localhost:3000 (Vite dev server with HMR)
- Backend: http://localhost:8000 (FastAPI with auto-reload)
- Proxy setup in `frontend/vite.config.ts` routes API calls to backend

## Testing & Debugging

### Web Application Testing
```bash
# Test full application stack
python run_web.py
# Open http://localhost:3000 and test with: https://blog.naver.com/kseta-inc/223963467411

# Test backend API directly
curl -X POST "http://localhost:8000/scrape" -H "Content-Type: application/json" -d '{"urls": ["https://blog.naver.com/kseta-inc/223963467411"], "headless": true}'

# Test standalone scraper
python standalone_scraper.py "https://blog.naver.com/kseta-inc/223963467411" --headless
```

### Frontend Development
```bash
cd frontend
npm run dev      # Start development server with hot reload
npm run build    # Build for production
npm run lint     # Run ESLint for code quality
```

### Backend Development
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
# API docs available at http://localhost:8000/docs
```

## Important Constraints

**Windows-Specific Issues**: The project is designed for Windows compatibility. On Windows, Playwright async subprocess execution fails, requiring process-based scraping via `standalone_scraper.py`.

**Legal Compliance**: This scraper respects robots.txt, implements rate limiting, and includes warnings about copyright and terms of service compliance.

**Technical Limitations**:
- Requires Playwright browsers installation (`playwright install chromium`)
- JavaScript-heavy blogs need sufficient wait times (handled automatically)
- Network timeouts handled with retry logic in process execution
- Some blogs may be protected or require authentication

**Port Management**: The `run_web.py` script automatically kills processes on ports 3000 and 8000 before starting to prevent conflicts.