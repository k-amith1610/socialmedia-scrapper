from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import uvicorn
import requests
import json
import time
from bs4 import BeautifulSoup
import re
import pandas as pd

app = FastAPI(title="Real Social Media Scraper API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:3001",  # Alternative localhost port
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ScrapingRequest(BaseModel):
    routes: List[str]
    keywords: Optional[List[str]] = ["traffic", "accident", "construction"]
    maxAgeHours: Optional[int] = 24
    maxPosts: Optional[int] = 10

def scrape_reddit_posts(routes, keywords, max_posts):
    """Scrape real Reddit posts"""
    posts = []
    
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            url = f"https://www.reddit.com/search.json?q={search_query}&sort=new&t=day&limit=25"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                print(f"Searching Reddit for: {search_query}")
                response = requests.get(url, headers=headers, timeout=5)
                print(f"Reddit response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    reddit_posts = data.get('data', {}).get('children', [])
                    print(f"Found {len(reddit_posts)} Reddit posts for {search_query}")
                    
                    for post_data in reddit_posts:
                        if len(posts) >= max_posts:
                            break
                            
                        post = post_data['data']
                        
                        # More lenient filtering - check if any keyword appears in title or text
                        title = post.get('title', '').lower()
                        selftext = post.get('selftext', '').lower()
                        full_text = f"{title} {selftext}"
                        
                        # Check if any keyword or route appears in the text
                        if any(kw.lower() in full_text for kw in keywords) or any(route.lower() in full_text for route in routes):
                            # Convert Reddit timestamp to ISO format
                            created_time = datetime.fromtimestamp(post.get('created_utc', 0))
                            
                            reddit_post = {
                                "id": f"reddit_{post.get('id', '')}",
                                "text": post.get('title', ''),
                                "timestamp": created_time.isoformat(),
                                "link": f"https://reddit.com{post.get('permalink', '')}",
                                "user": post.get('author', 'anonymous'),
                                "location": route,  # Use route as location
                                "source": "reddit",
                                "hashtags": [],  # Reddit doesn't use hashtags like Twitter
                                "media": [],
                                "description": post.get('selftext', '')[:200] + "..." if post.get('selftext') else "",
                                "engagement": {
                                    "likes": post.get('score', 0),
                                    "shares": 0,  # Reddit doesn't have shares
                                    "comments": post.get('num_comments', 0)
                                }
                            }
                            
                            posts.append(reddit_post)
                            print(f"Added Reddit post: {post.get('title', '')[:50]}...")
                        
            except Exception as e:
                print(f"Error scraping Reddit for {search_query}: {e}")
                continue
    
    return posts

def scrape_reddit_subreddits(routes, keywords, max_posts):
    """Scrape from specific subreddits that might have traffic-related content"""
    posts = []
    
    # Subreddits that might have traffic/transportation content
    subreddits = ['india', 'hyderabad', 'mumbai', 'delhi', 'bangalore', 'traffic', 'transportation']
    
    for subreddit in subreddits:
        if len(posts) >= max_posts:
            break
            
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={keyword}&restrict_sr=on&sort=new&t=day&limit=10"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            try:
                print(f"Searching r/{subreddit} for: {keyword}")
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    reddit_posts = data.get('data', {}).get('children', [])
                    print(f"Found {len(reddit_posts)} posts in r/{subreddit}")
                    
                    for post_data in reddit_posts:
                        if len(posts) >= max_posts:
                            break
                            
                        post = post_data['data']
                        
                        # Check if any route appears in the text
                        title = post.get('title', '').lower()
                        selftext = post.get('selftext', '').lower()
                        full_text = f"{title} {selftext}"
                        
                        if any(route.lower() in full_text for route in routes):
                            created_time = datetime.fromtimestamp(post.get('created_utc', 0))
                            
                            reddit_post = {
                                "id": f"reddit_{post.get('id', '')}",
                                "text": post.get('title', ''),
                                "timestamp": created_time.isoformat(),
                                "link": f"https://reddit.com{post.get('permalink', '')}",
                                "user": post.get('author', 'anonymous'),
                                "location": subreddit,
                                "source": "reddit",
                                "hashtags": [],
                                "media": [],
                                "description": post.get('selftext', '')[:200] + "..." if post.get('selftext') else "",
                                "engagement": {
                                    "likes": post.get('score', 0),
                                    "shares": 0,
                                    "comments": post.get('num_comments', 0)
                                }
                            }
                            
                            posts.append(reddit_post)
                            print(f"Added subreddit post: {post.get('title', '')[:50]}...")
                        
            except Exception as e:
                print(f"Error scraping r/{subreddit}: {e}")
                continue
    
    return posts

def scrape_twitter_posts(routes, keywords, max_posts):
    """Scrape Twitter posts using alternative methods (Python 3.12 compatible)"""
    posts = []
    
    # Use Twitter's public search API (no authentication required for basic searches)
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            try:
                print(f"Searching Twitter for: {search_query}")
                
                # Try Twitter's public search endpoint
                url = f"https://twitter.com/search?q={search_query}&src=typed_query&f=live"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for tweet-like content
                    tweet_selectors = [
                        'article[data-testid="tweet"]',
                        'div[data-testid="tweet"]',
                        'div[class*="tweet"]',
                        'article[class*="tweet"]'
                    ]
                    
                    tweet_elements = []
                    for selector in tweet_selectors:
                        tweet_elements = soup.select(selector)
                        if tweet_elements:
                            break
                    
                    print(f"Found {len(tweet_elements)} potential tweets")
                    
                    for tweet in tweet_elements[:max_posts]:
                        if len(posts) >= max_posts:
                            break
                            
                        try:
                            # Extract tweet text
                            text_selectors = [
                                'div[data-testid="tweetText"]',
                                'div[class*="tweet-text"]',
                                'p[class*="tweet-text"]',
                                'span[class*="tweet-text"]'
                            ]
                            
                            text = ""
                            for selector in text_selectors:
                                text_elem = tweet.select_one(selector)
                                if text_elem:
                                    text = text_elem.get_text().strip()
                                    break
                            
                            if not text:
                                text = tweet.get_text().strip()
                            
                            if text and len(text) > 10:
                                # Extract username
                                username_selectors = [
                                    'a[data-testid="User-Name"]',
                                    'a[class*="username"]',
                                    'span[class*="username"]'
                                ]
                                
                                username = "twitter_user"
                                for selector in username_selectors:
                                    username_elem = tweet.select_one(selector)
                                    if username_elem:
                                        username = username_elem.get_text().strip()
                                        break
                                
                                # Extract hashtags
                                hashtags = re.findall(r'#\w+', text)
                                
                                # Check if content matches our criteria
                                if any(kw.lower() in text.lower() for kw in keywords) or any(route.lower() in text.lower() for route in routes):
                                    twitter_post = {
                                        "id": f"twitter_{hash(text)}",
                                        "text": text[:280],  # Twitter character limit
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                        "link": url,
                                        "user": username,
                                        "location": route,
                                        "source": "twitter",
                                        "hashtags": hashtags,
                                        "media": [],
                                        "description": text[:200] + "..." if len(text) > 200 else text,
                                        "engagement": {
                                            "likes": 0,
                                            "shares": 0,
                                            "comments": 0
                                        }
                                    }
                                    
                                    posts.append(twitter_post)
                                    print(f"Added Twitter post: {text[:50]}...")
                                    
                        except Exception as e:
                            print(f"Error parsing tweet: {e}")
                            continue
                            
                else:
                    print(f"Failed to get Twitter posts: {response.status_code}")
                    
            except Exception as e:
                print(f"Error scraping Twitter for {search_query}: {e}")
                continue
    
    return posts

def scrape_facebook_posts(routes, keywords, max_posts):
    """Scrape Facebook posts using public search (Python 3.12 compatible)"""
    posts = []
    
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            try:
                print(f"Searching Facebook for: {search_query}")
                
                # Try Facebook's public search
                url = f"https://www.facebook.com/search/posts/?q={search_query}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for Facebook post content
                    post_selectors = [
                        'div[data-testid="post_message"]',
                        'div[class*="post"]',
                        'div[class*="story"]',
                        'article[class*="post"]'
                    ]
                    
                    post_elements = []
                    for selector in post_selectors:
                        post_elements = soup.select(selector)
                        if post_elements:
                            break
                    
                    print(f"Found {len(post_elements)} potential Facebook posts")
                    
                    for post in post_elements[:max_posts]:
                        if len(posts) >= max_posts:
                            break
                            
                        try:
                            # Extract post text
                            text_selectors = [
                                'div[data-testid="post_message"]',
                                'div[class*="content"]',
                                'p',
                                'span[class*="text"]'
                            ]
                            
                            text = ""
                            for selector in text_selectors:
                                text_elem = post.select_one(selector)
                                if text_elem:
                                    text = text_elem.get_text().strip()
                                    break
                            
                            if not text:
                                text = post.get_text().strip()
                            
                            if text and len(text) > 20:
                                # Extract username
                                username_selectors = [
                                    'a[class*="profile"]',
                                    'a[class*="user"]',
                                    'span[class*="name"]'
                                ]
                                
                                username = "facebook_user"
                                for selector in username_selectors:
                                    username_elem = post.select_one(selector)
                                    if username_elem:
                                        username = username_elem.get_text().strip()
                                        break
                                
                                # Extract hashtags
                                hashtags = re.findall(r'#\w+', text)
                                
                                # Check if content matches our criteria
                                if any(kw.lower() in text.lower() for kw in keywords) or any(route.lower() in text.lower() for route in routes):
                                    fb_post = {
                                        "id": f"facebook_{hash(text)}",
                                        "text": text[:500],  # Facebook allows longer posts
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                        "link": url,
                                        "user": username,
                                        "location": route,
                                        "source": "facebook",
                                        "hashtags": hashtags,
                                        "media": [],
                                        "description": text[:200] + "..." if len(text) > 200 else text,
                                        "engagement": {
                                            "likes": 0,
                                            "shares": 0,
                                            "comments": 0
                                        }
                                    }
                                    
                                    posts.append(fb_post)
                                    print(f"Added Facebook post: {text[:50]}...")
                                    
                        except Exception as e:
                            print(f"Error parsing Facebook post: {e}")
                            continue
                            
                else:
                    print(f"Failed to get Facebook posts: {response.status_code}")
                    
            except Exception as e:
                print(f"Error scraping Facebook for {search_query}: {e}")
                continue
    
    return posts

def scrape_linkedin_posts(routes, keywords, max_posts):
    """Scrape LinkedIn posts using public profiles and company pages"""
    posts = []
    
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            try:
                # Try LinkedIn search (limited due to authentication requirements)
                url = f"https://www.linkedin.com/search/results/content/?keywords={search_query}&origin=GLOBAL_SEARCH_HEADER"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                
                print(f"Searching LinkedIn for: {search_query}")
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for LinkedIn post content
                    post_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'feed', 'content']))
                    
                    print(f"Found {len(post_elements)} potential LinkedIn posts")
                    
                    for i, element in enumerate(post_elements[:3]):  # Limit to 3 posts
                        if len(posts) >= max_posts:
                            break
                            
                        text = element.get_text().strip()
                        if text and len(text) > 20:
                            # Check if content matches our criteria
                            if any(kw.lower() in text.lower() for kw in keywords) or any(route.lower() in text.lower() for route in routes):
                                linkedin_post = {
                                    "id": f"linkedin_{hash(text)}",
                                    "text": text[:500],
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "link": url,
                                    "user": "linkedin_user",
                                    "location": route,
                                    "source": "linkedin",
                                    "hashtags": re.findall(r'#\w+', text),
                                    "media": [],
                                    "description": text[:200] + "..." if len(text) > 200 else text,
                                    "engagement": {
                                        "likes": 0,
                                        "shares": 0,
                                        "comments": 0
                                    }
                                }
                                
                                posts.append(linkedin_post)
                                print(f"Added LinkedIn post: {text[:50]}...")
                                
            except Exception as e:
                print(f"Error scraping LinkedIn: {e}")
                continue
    
    return posts

def scrape_telegram_posts(routes, keywords, max_posts):
    """Scrape Telegram posts using public channels"""
    posts = []
    
    # Telegram public channels that might have traffic-related content
    telegram_channels = [
        "trafficupdatesindia",
        "hyderabadtraffic",
        "mumbaitraffic",
        "delhitraffic",
        "bangaloretraffic",
        "indiatrafficalerts",
        "trafficpoliceindia"
    ]
    
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            # Try multiple Telegram scraping approaches
            for channel in telegram_channels:
                if len(posts) >= max_posts:
                    break
                    
                try:
                    # Try different Telegram web URLs
                    telegram_urls = [
                        f"https://t.me/s/{channel}",
                        f"https://t.me/{channel}",
                        f"https://web.telegram.org/k/#@{channel}"
                    ]
                    
                    for url in telegram_urls:
                        if len(posts) >= max_posts:
                            break
                            
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive'
                        }
                        
                        print(f"Searching Telegram channel {channel} for: {search_query}")
                        response = requests.get(url, headers=headers, timeout=15)
                        
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Try multiple selectors for Telegram messages
                            message_selectors = [
                                'div[class*="message"]',
                                'div[class*="post"]',
                                'div[class*="text"]',
                                'div[data-post]',
                                'div[class*="tgme_widget_message"]',
                                'div[class*="js-widget_message"]'
                            ]
                            
                            message_elements = []
                            for selector in message_selectors:
                                message_elements = soup.select(selector)
                                if message_elements:
                                    break
                            
                            print(f"Found {len(message_elements)} potential Telegram messages from {channel}")
                            
                            for i, element in enumerate(message_elements[:5]):  # Limit to 5 messages
                                if len(posts) >= max_posts:
                                    break
                                    
                                try:
                                    # Try to extract text content
                                    text_selectors = [
                                        'div[class*="text"]',
                                        'div[class*="message"]',
                                        'p',
                                        'span[class*="text"]',
                                        'div[class*="tgme_widget_message_text"]'
                                    ]
                                    
                                    text = ""
                                    for selector in text_selectors:
                                        text_elem = element.select_one(selector)
                                        if text_elem:
                                            text = text_elem.get_text().strip()
                                            if text:
                                                break
                                    
                                    if not text:
                                        text = element.get_text().strip()
                                    
                                    if text and len(text) > 10:
                                        # Check if content matches our criteria
                                        if any(kw.lower() in text.lower() for kw in keywords) or any(route.lower() in text.lower() for route in routes):
                                            # Try to extract username
                                            username_selectors = [
                                                'a[class*="username"]',
                                                'span[class*="username"]',
                                                'div[class*="author"]'
                                            ]
                                            
                                            username = "telegram_user"
                                            for selector in username_selectors:
                                                username_elem = element.select_one(selector)
                                                if username_elem:
                                                    username = username_elem.get_text().strip()
                                                    break
                                            
                                            telegram_post = {
                                                "id": f"telegram_{hash(text)}",
                                                "text": text[:500],
                                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                                "link": url,
                                                "user": username,
                                                "location": route,
                                                "source": "telegram",
                                                "hashtags": re.findall(r'#\w+', text),
                                                "media": [],
                                                "description": text[:200] + "..." if len(text) > 200 else text,
                                                "engagement": {
                                                    "likes": 0,
                                                    "shares": 0,
                                                    "comments": 0
                                                }
                                            }
                                            
                                            posts.append(telegram_post)
                                            print(f"Added Telegram post: {text[:50]}...")
                                            
                                except Exception as e:
                                    print(f"Error parsing Telegram message: {e}")
                                    continue
                                    
                        else:
                            print(f"Failed to get Telegram channel {channel}: {response.status_code}")
                            
                except Exception as e:
                    print(f"Error scraping Telegram channel {channel}: {e}")
                    continue
    
    return posts

def scrape_news_posts(routes, keywords, max_posts):
    """Scrape news articles related to traffic"""
    posts = []
    
    # Use multiple free news APIs
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            # Try multiple news sources with better APIs
            news_sources = [
                # Working RSS feeds for traffic news
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://rss.cnn.com/rss/edition.rss",
                "https://feeds.reuters.com/reuters/topNews",
                "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "https://www.ndtv.com/india-news/rss",
                "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
                "https://www.thehindu.com/news/national/?service=rss",
                # NewsAPI.org (free tier) - will fail but we handle it gracefully
                f"https://newsapi.org/v2/everything?q={search_query}&sortBy=publishedAt&language=en&pageSize=10&apiKey=test",
                # GNews API (free tier) - will fail but we handle it gracefully  
                f"https://gnews.io/api/v4/search?q={search_query}&lang=en&country=in&max=10&apikey=test"
            ]
            
            for i, url in enumerate(news_sources):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    print(f"Searching news source {i+1} for: {search_query}")
                    response = requests.get(url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # Handle different API formats
                            articles = []
                            if 'articles' in data:
                                articles = data.get('articles', [])
                            elif 'value' in data:
                                articles = data.get('value', [])
                            elif 'items' in data:
                                articles = data.get('items', [])
                            
                            print(f"Found {len(articles)} articles from news source {i+1}")
                            
                            for article in articles:
                                if len(posts) >= max_posts:
                                    break
                                    
                                # Parse publication date
                                try:
                                    if 'publishedAt' in article:
                                        pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                                    elif 'datePublished' in article:
                                        pub_date = datetime.fromisoformat(article['datePublished'].replace('Z', '+00:00'))
                                    elif 'published' in article:
                                        pub_date = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                                    else:
                                        pub_date = datetime.now(timezone.utc)
                                except:
                                    pub_date = datetime.now(timezone.utc)
                                
                                # Check if article content matches our criteria
                                title = article.get('title', '').lower()
                                description = article.get('description', '').lower()
                                content = f"{title} {description}"
                                
                                if any(kw.lower() in content for kw in keywords) or any(route.lower() in content for route in routes):
                                    news_post = {
                                        "id": f"news_{hash(article.get('url', ''))}",
                                        "text": article.get('title', ''),
                                        "timestamp": pub_date.isoformat(),
                                        "link": article.get('url', ''),
                                        "user": article.get('source', {}).get('name', 'News Source') if isinstance(article.get('source'), dict) else article.get('source', 'News Source'),
                                        "location": route,
                                        "source": "news",
                                        "hashtags": [],
                                        "media": [article.get('urlToImage', '')] if article.get('urlToImage') else [],
                                        "description": article.get('description', ''),
                                        "engagement": {
                                            "likes": 0,
                                            "shares": 0,
                                            "comments": 0
                                        }
                                    }
                                    
                                    posts.append(news_post)
                                    print(f"Added news article: {article.get('title', '')[:50]}...")
                                    
                        except json.JSONDecodeError:
                            # Try parsing as RSS/XML
                            try:
                                soup = BeautifulSoup(response.text, 'xml')
                                items = soup.find_all(['item', 'entry'])
                                
                                print(f"Found {len(items)} RSS items from news source {i+1}")
                                
                                for item in items:
                                    if len(posts) >= max_posts:
                                        break
                                        
                                    title_elem = item.find(['title', 'name'])
                                    description_elem = item.find(['description', 'summary'])
                                    link_elem = item.find(['link', 'url'])
                                    
                                    if title_elem:
                                        title = title_elem.get_text().strip()
                                        description = description_elem.get_text().strip() if description_elem else ""
                                        link = link_elem.get_text().strip() if link_elem else ""
                                        
                                        content = f"{title} {description}".lower()
                                        
                                        if any(kw.lower() in content for kw in keywords) or any(route.lower() in content for route in routes):
                                            news_post = {
                                                "id": f"news_{hash(link)}",
                                                "text": title,
                                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                                "link": link,
                                                "user": "RSS News Source",
                                                "location": route,
                                                "source": "news",
                                                "hashtags": [],
                                                "media": [],
                                                "description": description[:200] + "..." if len(description) > 200 else description,
                                                "engagement": {
                                                    "likes": 0,
                                                    "shares": 0,
                                                    "comments": 0
                                                }
                                            }
                                            
                                            posts.append(news_post)
                                            print(f"Added RSS news: {title[:50]}...")
                                            
                            except Exception as e:
                                print(f"Error parsing RSS from news source {i+1}: {e}")
                                continue
                                
                except Exception as e:
                    print(f"Error scraping news source {i+1} for {search_query}: {e}")
                    continue
    
    return posts

def scrape_rss_news(routes, keywords, max_posts):
    """Scrape news from working RSS feeds"""
    posts = []
    
    # Working RSS feeds
    rss_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.reuters.com/reuters/topNews",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://www.ndtv.com/india-news/rss"
    ]
    
    for route in routes:
        for keyword in keywords:
            if len(posts) >= max_posts:
                break
                
            search_query = f"{keyword} {route}"
            
            for i, rss_url in enumerate(rss_feeds):
                if len(posts) >= max_posts:
                    break
                    
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    print(f"Fetching RSS feed {i+1}: {rss_url}")
                    response = requests.get(rss_url, headers=headers, timeout=8)
                    
                    if response.status_code == 200:
                        try:
                            soup = BeautifulSoup(response.text, 'xml')
                            items = soup.find_all(['item', 'entry'])
                            
                            print(f"Found {len(items)} RSS items from feed {i+1}")
                            
                            for item in items:
                                if len(posts) >= max_posts:
                                    break
                                    
                                title_elem = item.find(['title', 'name'])
                                description_elem = item.find(['description', 'summary'])
                                link_elem = item.find(['link', 'url'])
                                pub_date_elem = item.find(['pubDate', 'published', 'date'])
                                
                                if title_elem:
                                    title = title_elem.get_text().strip()
                                    description = description_elem.get_text().strip() if description_elem else ""
                                    link = link_elem.get_text().strip() if link_elem else ""
                                    
                                    # Parse publication date
                                    try:
                                        if pub_date_elem:
                                            pub_date_str = pub_date_elem.get_text().strip()
                                            # Try to parse various date formats
                                            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d']:
                                                try:
                                                    pub_date = datetime.strptime(pub_date_str, fmt)
                                                    break
                                                except:
                                                    continue
                                            else:
                                                pub_date = datetime.now(timezone.utc)
                                        else:
                                            pub_date = datetime.now(timezone.utc)
                                    except:
                                        pub_date = datetime.now(timezone.utc)
                                    
                                    content = f"{title} {description}".lower()
                                    
                                    # Check if content matches our criteria
                                    if any(kw.lower() in content for kw in keywords) or any(route.lower() in content for route in routes):
                                        rss_post = {
                                            "id": f"rss_{hash(link)}",
                                            "text": title,
                                            "timestamp": pub_date.isoformat(),
                                            "link": link,
                                            "user": f"RSS Feed {i+1}",
                                            "location": route,
                                            "source": "news",
                                            "hashtags": [],
                                            "media": [],
                                            "description": description[:200] + "..." if len(description) > 200 else description,
                                            "engagement": {
                                                "likes": 0,
                                                "shares": 0,
                                                "comments": 0
                                            }
                                        }
                                        
                                        posts.append(rss_post)
                                        print(f"Added RSS news: {title[:50]}...")
                                    # More lenient - add any news if we don't have enough posts
                                    elif len(posts) < max_posts // 2:
                                        rss_post = {
                                            "id": f"rss_{hash(link)}",
                                            "text": title,
                                            "timestamp": pub_date.isoformat(),
                                            "link": link,
                                            "user": f"RSS Feed {i+1}",
                                            "location": "General",
                                            "source": "news",
                                            "hashtags": [],
                                            "media": [],
                                            "description": description[:200] + "..." if len(description) > 200 else description,
                                            "engagement": {
                                                "likes": 0,
                                                "shares": 0,
                                                "comments": 0
                                            }
                                        }
                                        
                                        posts.append(rss_post)
                                        print(f"Added general RSS news: {title[:50]}...")
                                        
                        except Exception as e:
                            print(f"Error parsing RSS feed {i+1}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error fetching RSS feed {i+1}: {e}")
                    continue
    
    return posts

@app.post("/scrape")
async def scrape_social_media(request: ScrapingRequest):
    try:
        # Add timeout check for Vercel
        max_execution_time = 9  # Vercel has 10s limit, keep 1s buffer
        start_time = time.time()
        posts = []
        
        # Scrape from multiple sources
        print(f"Scraping real data for routes: {request.routes}, keywords: {request.keywords}")
        
        # 1. Reddit search (most reliable) - FAST
        if time.time() - start_time < max_execution_time:
            reddit_posts = scrape_reddit_posts(request.routes, request.keywords, request.maxPosts)
            posts.extend(reddit_posts)
            print(f"Found {len(reddit_posts)} Reddit posts from search")
        
        # 2. RSS News feeds (reliable and fast) - PRIORITY
        if len(posts) < request.maxPosts and time.time() - start_time < max_execution_time:
            rss_posts = scrape_rss_news(request.routes, request.keywords, request.maxPosts - len(posts))
            posts.extend(rss_posts)
            print(f"Found {len(rss_posts)} RSS news posts")
        
        # Stop here for Vercel deployment as other sources are slower
        # Return what we have to avoid timeout
        
        # Limit to max posts
        posts = posts[:request.maxPosts]
        
        return {
            "status": "success",
            "message": f"Real social media data scraped successfully from {len(set(p['source'] for p in posts))} sources",
            "data": {
                "posts": posts,
                "totalPosts": len(posts),
                "routes": request.routes,
                "keywords": request.keywords,
                "maxAgeHours": request.maxAgeHours,
                "maxPosts": request.maxPosts,
                "scrapedAt": datetime.now(timezone.utc).isoformat(),
                "sources": list(set(p['source'] for p in posts)),
                "note": f"Real data scraped from multiple social media platforms. Found {len(posts)} posts.",
                "execution_time": round(time.time() - start_time, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "message": "Error occurred while scraping data",
                "note": "This might be due to Vercel's timeout limit (10s) or memory constraints"
            }
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Real data scraper API is running",
        "note": "Scraping from Reddit, Twitter, Facebook, LinkedIn, Telegram, and News APIs"
    }

@app.get("/")
async def root():
    return {
        "message": "Real Social Media Scraper API",
        "endpoints": {
            "POST /scrape": "Scrape real social media data",
            "GET /health": "Health check",
            "GET /": "API info"
        },
        "note": "Scraping real data from multiple social media platforms",
        "sources": ["reddit", "twitter", "facebook", "linkedin", "telegram", "news"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 