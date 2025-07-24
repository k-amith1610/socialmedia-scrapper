# Real Social Media Scraper API

A FastAPI-based social media scraper that provides **real data** from Reddit and news sources.

## 🎯 Features

- ✅ **Real Data Scraping** - No mock data, actual social media posts
- ✅ **Reddit Integration** - Scrapes real Reddit posts with engagement metrics
- ✅ **News API Integration** - Fetches real news articles
- ✅ **Multiple Sources** - Reddit search + subreddits + news APIs
- ✅ **Location-based Filtering** - Search by specific routes/cities
- ✅ **Keyword Filtering** - Filter by traffic, accident, construction, etc.
- ✅ **Real Engagement Metrics** - Actual likes, comments, scores
- ✅ **Perfect JSON Format** - Matches your SocialMediaPost interface

## 🚀 Quick Start

### Prerequisites

- Python 3.13 or higher
- uv package manager (faster and more reliable than pip)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd socialmedia-scrapper

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment (optional but recommended)
uv venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies using uv (much faster than pip)
uv pip install .

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`

## 🔧 API Endpoints

### POST `/scrape` - Main Scraping Endpoint

**Request:**

```json
{
  "routes": ["Hyderabad", "Mumbai"],
  "keywords": ["traffic", "accident"],
  "maxAgeHours": 24,
  "maxPosts": 10
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Real social media data scraped successfully from 1 sources",
  "data": {
    "posts": [
      {
        "id": "reddit_1m4nliv",
        "text": "Need cycling routes in Hyderabad",
        "timestamp": "2025-07-20T17:52:19",
        "link": "https://reddit.com/r/india_cycling/comments/1m4nliv/...",
        "user": "kakkarotssj",
        "location": "Hyderabad",
        "source": "reddit",
        "hashtags": [],
        "media": [],
        "description": "Hey, folks of Hyderabad...",
        "engagement": {
          "likes": 3,
          "shares": 0,
          "comments": 0
        }
      }
    ],
    "totalPosts": 5,
    "routes": ["Hyderabad"],
    "keywords": ["traffic"],
    "maxAgeHours": 24,
    "maxPosts": 10,
    "scrapedAt": "2025-07-20T13:00:45.977478",
    "sources": ["reddit"],
    "note": "Real data scraped from Reddit and News APIs. Found 5 posts."
  }
}
```

### GET `/health` - Health Check

```bash
curl http://localhost:8000/health
```

### GET `/` - API Information

```bash
curl http://localhost:8000/
```

## 🧪 Testing

### Test with curl

```bash
# Basic test
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "routes": ["Hyderabad"],
    "keywords": ["traffic"],
    "maxPosts": 5
  }'

# Multiple cities test
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "routes": ["Hyderabad", "Mumbai"],
    "keywords": ["traffic", "accident"],
    "maxPosts": 10
  }'
```

## 📊 Data Sources

### Reddit

- **Search API** - Searches all of Reddit for keywords + routes
- **Subreddit Search** - Searches specific subreddits (india, hyderabad, mumbai, etc.)
- **Real Data** - Actual usernames, engagement metrics, timestamps

### News APIs

- **NewsAPI.org** - Traffic and transportation news
- **GNews** - Local news articles
- **Real Articles** - Actual news content with sources

## 🔗 Integration with Next.js

### Environment Variable

```
PYTHON_API_URL=http://localhost:8000
```

### JavaScript Example

```javascript
const response = await fetch("http://localhost:8000/scrape", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    routes: ["Hyderabad"],
    keywords: ["traffic"],
    maxPosts: 5,
  }),
});

const data = await response.json();
console.log(data.data.posts); // Real social media posts
```

## 📁 Project Structure

```
socialmedia-scrapper/
├── main.py              # Main FastAPI application
├── pyproject.toml       # Python project configuration and dependencies
├── uv.lock             # Lock file for uv dependency management
├── .python-version      # Python version specification
├── .venv/              # Virtual environment directory
├── .gitignore          # Git ignore configuration
└── README.md           # Project documentation
```

## 🎯 Key Benefits

- **Real Data** - No mock data, actual social media posts
- **Fast** - No browser automation overhead
- **Reliable** - Multiple data sources for redundancy
- **Scalable** - Easy to add more platforms
- **Production Ready** - Can be deployed to Railway/Render/Heroku
- **Modern Tooling** - Uses uv for fast, reliable dependency management

## 🚀 Deployment

### Local Development

```bash
python main.py
```

### Vercel Deployment

1. Install Vercel CLI:

```bash
npm install -g vercel
```

2. Login to Vercel:

```bash
vercel login
```

3. Deploy to Vercel:

```bash
vercel
```

4. For production deployment:

```bash
vercel --prod
```

The deployment will provide you with a URL where your API is accessible.

#### Important Notes for Vercel Deployment:

- The free tier has a 10-second execution limit
- Serverless functions have cold starts
- Environment variables should be configured in the Vercel dashboard
- API routes will be available at `https://your-project.vercel.app/api/`

### Other Deployment Options

You can also deploy to other platforms:

- Railway
- Render
- Heroku
- DigitalOcean App Platform

### Environment Setup

Make sure to set up the following environment variables in your deployment environment:

- `PORT` - Port number for the FastAPI server (default: 8000)
- Add any other required API keys or configuration variables

### Development Notes

- We use `uv` for dependency management instead of pip for better performance and reliability
- The `uv.lock` file ensures reproducible installations across different environments
- Dependencies are specified in `pyproject.toml` and locked in `uv.lock`
- For Vercel deployment, we maintain a separate `requirements.txt`

The API is production-ready and will work with real data immediately! 🎉
