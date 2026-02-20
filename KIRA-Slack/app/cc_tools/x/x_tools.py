"""
X (Twitter) Tools for Claude Code SDK
Tools that allow Claude to use X (Twitter)
"""

import json
import os
import re
from typing import Any, Dict, Optional

import httpx
import tweepy
from claude_agent_sdk import create_sdk_mcp_server, tool

from app.config.settings import get_settings
from app.cc_utils.x_helper import get_valid_access_token


# OAuth 1.0a client (for posting tweets, media upload, timeline)
_x_client_v2: Optional[tweepy.Client] = None
_x_client_v1: Optional[tweepy.API] = None


def get_x_client_v2() -> tweepy.Client:
    """Return X API v2 client (OAuth 1.0a)"""
    global _x_client_v2
    if _x_client_v2 is None:
        raise ValueError("X client not initialized. Call initialize_x_client() first.")
    return _x_client_v2


def get_x_client_v1() -> tweepy.API:
    """Return X API v1.1 client (for media upload)"""
    global _x_client_v1
    if _x_client_v1 is None:
        raise ValueError("X client not initialized. Call initialize_x_client() first.")
    return _x_client_v1


def initialize_x_client():
    """Initialize X client (OAuth 1.0a)"""
    global _x_client_v2, _x_client_v1

    settings = get_settings()

    if not all([
        settings.X_API_KEY,
        settings.X_API_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    ]):
        raise ValueError("X API OAuth 1.0a credentials not set in settings")

    # API v2 client
    _x_client_v2 = tweepy.Client(
        consumer_key=settings.X_API_KEY,
        consumer_secret=settings.X_API_SECRET,
        access_token=settings.X_ACCESS_TOKEN,
        access_token_secret=settings.X_ACCESS_TOKEN_SECRET,
    )

    # API v1.1 client (for media upload)
    auth = tweepy.OAuth1UserHandler(
        settings.X_API_KEY,
        settings.X_API_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    )
    _x_client_v1 = tweepy.API(auth)

    return _x_client_v2


@tool(
    "post_tweet",
    "Posts a tweet. Important: There is a 280 character limit, so summarize long content to within 250 characters.",
    {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Tweet content (max 280 chars, recommended to stay within 250)"}
        },
        "required": ["text"],
    },
)
async def x_post_tweet(args: Dict[str, Any]) -> Dict[str, Any]:
    """Post a tweet (OAuth 1.0a)"""
    text = args["text"]

    try:
        import logging
        logging.info(f"[X_TOOL] Attempting to post tweet: {text[:50]}...")

        client = get_x_client_v2()
        response = client.create_tweet(text=text)

        tweet_data = response.data
        tweet_id = tweet_data.get("id")
        tweet_text = tweet_data.get("text")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": "Tweet posted successfully",
                            "tweet_id": tweet_id,
                            "tweet_text": tweet_text,
                            "tweet_url": f"https://twitter.com/i/web/status/{tweet_id}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except Exception as e:
        import logging
        logging.error(f"[X_TOOL] Tweet post error: {type(e).__name__}: {e}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to post tweet: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "get_tweet",
    "Retrieves the content of a specific tweet. Enter a tweet URL or tweet ID.",
    {
        "type": "object",
        "properties": {
            "tweet_url_or_id": {
                "type": "string",
                "description": "Tweet URL (e.g., https://x.com/username/status/1234567890) or tweet ID (e.g., 1234567890)",
            }
        },
        "required": ["tweet_url_or_id"],
    },
)
async def x_get_tweet(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve tweet content"""
    tweet_url_or_id = args["tweet_url_or_id"]

    try:
        # Use OAuth 2.0 User Context token
        access_token = await get_valid_access_token()
        if not access_token:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": True,
                                "message": "X authentication required. Please authenticate via /bot/auth/x/start in the web interface.",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "error": True,
            }

        # Extract tweet_id from URL or use ID as-is
        tweet_id = tweet_url_or_id

        # Extract ID if URL format
        url_pattern = (
            r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/(?:\w+)/status/(\d+)"
        )
        match = re.search(url_pattern, tweet_url_or_id)
        if match:
            tweet_id = match.group(1)

        # v2 API 직접 호출: GET /2/tweets/:id
        url = f"https://api.twitter.com/2/tweets/{tweet_id}"

        params = {
            "tweet.fields": "created_at,public_metrics,author_id,text",
            "expansions": "author_id",
            "user.fields": "username,name"
        }

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": True,
                                "message": "Tweet not found.",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "error": True,
            }

        tweet = data["data"]

        # Get author information
        author_username = "unknown"
        author_name = "Unknown"
        if data.get("includes") and data["includes"].get("users"):
            author = data["includes"]["users"][0]
            author_username = author.get("username", "unknown")
            author_name = author.get("name", "Unknown")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": "Successfully retrieved tweet content.",
                            "tweet": {
                                "id": tweet["id"],
                                "text": tweet.get("text", ""),
                                "author": {
                                    "username": author_username,
                                    "name": author_name,
                                },
                                "created_at": tweet.get("created_at", ""),
                                "metrics": tweet.get("public_metrics", {}),
                                "url": f"https://twitter.com/{author_username}/status/{tweet['id']}",
                            },
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve tweet (HTTP {e.response.status_code}): {error_detail}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve tweet: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "get_my_tweets",
    "Retrieves a list of recent tweets I have posted.",
    {
        "type": "object",
        "properties": {
            "max_results": {
                "type": "integer",
                "description": "Number of tweets to retrieve (default: 10, max: 100)",
            }
        },
    },
)
async def x_get_my_tweets(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve my posted tweets"""
    max_results = args.get("max_results", 10)

    # max_results limit (5-100)
    max_results = max(5, min(100, max_results))

    try:
        # Use OAuth 2.0 User Context token
        access_token = await get_valid_access_token()
        if not access_token:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": True,
                                "message": "X authentication required. Please authenticate via /bot/auth/x/start in the web interface.",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "error": True,
            }

        # Set OAuth 2.0 headers
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with httpx.AsyncClient() as http_client:
            # First get my user_id (OAuth 2.0)
            me_response = await http_client.get(
                "https://api.twitter.com/2/users/me",
                headers=headers
            )
            me_response.raise_for_status()
            my_user_id = me_response.json()["data"]["id"]

            # v2 API 직접 호출: GET /2/users/:id/tweets
            url = f"https://api.twitter.com/2/users/{my_user_id}/tweets"

            params = {
                "max_results": max_results,
                "tweet.fields": "created_at,public_metrics,text"
            }
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "message": "No tweets posted.",
                                "tweets": [],
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

        tweets = []
        for tweet in data["data"]:
            tweets.append(
                {
                    "id": tweet["id"],
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at", ""),
                    "metrics": tweet.get("public_metrics", {}),
                    "url": f"https://twitter.com/i/web/status/{tweet['id']}",
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": f"Retrieved {len(tweets)} tweets.",
                            "count": len(tweets),
                            "tweets": tweets,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve tweet (HTTP {e.response.status_code}): {error_detail}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve tweet: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "search_recent_tweets",
    "Searches for tweets from the last 7 days by keyword.",
    {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword or query (e.g., 'claude code', 'from:username', '#hashtag')",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of tweets to retrieve (default: 10, max: 100)",
            },
        },
        "required": ["query"],
    },
)
async def x_search_recent_tweets(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search recent tweets (within 7 days)"""
    query = args["query"]
    max_results = args.get("max_results", 10)

    # max_results limit (10-100)
    max_results = max(10, min(100, max_results))

    try:
        # Use OAuth 2.0 User Context token
        access_token = await get_valid_access_token()
        if not access_token:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": True,
                                "message": "X authentication required. Please authenticate via /bot/auth/x/start in the web interface.",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "error": True,
            }

        # v2 API 직접 호출: GET /2/tweets/search/recent
        url = "https://api.twitter.com/2/tweets/search/recent"

        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id,text",
            "expansions": "author_id",
            "user.fields": "username,name"
        }

        # OAuth 2.0 User Context token headers
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "message": f"No search results for '{query}'.",
                                "tweets": [],
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

        # Map author information
        authors = {}
        if data.get("includes") and data["includes"].get("users"):
            for user in data["includes"]["users"]:
                authors[user["id"]] = {
                    "username": user.get("username", "unknown"),
                    "name": user.get("name", "Unknown")
                }

        tweets = []
        for tweet in data["data"]:
            author_info = authors.get(
                tweet.get("author_id"), {"username": "unknown", "name": "Unknown"}
            )
            tweets.append(
                {
                    "id": tweet["id"],
                    "text": tweet.get("text", ""),
                    "author": author_info,
                    "created_at": tweet.get("created_at", ""),
                    "metrics": tweet.get("public_metrics", {}),
                    "url": f"https://twitter.com/{author_info['username']}/status/{tweet['id']}",
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": f"Found {len(tweets)} tweets for '{query}'.",
                            "query": query,
                            "count": len(tweets),
                            "tweets": tweets,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Tweet search failed (HTTP {e.response.status_code}): {error_detail}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Tweet search failed: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "post_tweet_with_media",
    "Posts a tweet with a photo. Important: There is a 280 character limit, so summarize long content to within 250 characters.",
    {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Tweet content (max 280 chars, recommended to stay within 250)"},
            "image_path": {
                "type": "string",
                "description": "Absolute path to the image file to upload (e.g., FILESYSTEM_BASE_DIR/files/image.png)",
            },
        },
        "required": ["text", "image_path"],
    },
)
async def x_post_tweet_with_media(args: Dict[str, Any]) -> Dict[str, Any]:
    """Post a tweet with photo (OAuth 1.0a)"""
    text = args["text"]
    image_path = args["image_path"]

    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": True,
                                "message": f"Image file not found: {image_path}",
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "error": True,
            }

        # Media upload (API v1.1)
        client_v1 = get_x_client_v1()
        media = client_v1.media_upload(filename=image_path)
        media_id = media.media_id

        # Post tweet (API v2)
        client_v2 = get_x_client_v2()
        response = client_v2.create_tweet(text=text, media_ids=[media_id])

        tweet_data = response.data
        tweet_id = tweet_data.get("id")
        tweet_text = tweet_data.get("text")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": "Tweet with photo posted successfully",
                            "tweet_id": tweet_id,
                            "tweet_text": tweet_text,
                            "media_id": str(media_id),
                            "tweet_url": f"https://twitter.com/i/web/status/{tweet_id}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to post tweet: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


@tool(
    "get_home_timeline",
    "Retrieves the home timeline (recent tweet feed from people you follow).",
    {
        "type": "object",
        "properties": {
            "max_results": {
                "type": "integer",
                "description": "Number of tweets to retrieve (default: 10, max: 100)",
            }
        },
    },
)
async def x_get_home_timeline(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve home timeline (OAuth 1.0a)"""
    max_results = args.get("max_results", 10)
    max_results = max(5, min(100, max_results))

    try:
        client = get_x_client_v2()

        # First get my user_id
        me = client.get_me()
        my_user_id = me.data.id

        # API v2: GET /2/users/:id/timelines/reverse_chronological
        url = f"https://api.twitter.com/2/users/{my_user_id}/timelines/reverse_chronological"

        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id,text",
            "expansions": "author_id",
            "user.fields": "username,name",
        }

        # Generate OAuth 1.0a auth headers
        from requests_oauthlib import OAuth1
        import requests

        settings = get_settings()
        auth = OAuth1(
            settings.X_API_KEY,
            settings.X_API_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        )

        async with httpx.AsyncClient() as http_client:
            # requests로 서명 생성
            req = requests.Request("GET", url, params=params, auth=auth)
            prepared = req.prepare()

            # httpx로 요청
            response = await http_client.get(prepared.url, headers=prepared.headers)
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": True,
                                "message": "No tweets in home timeline.",
                                "tweets": [],
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }

        # Map author information
        authors = {}
        if data.get("includes") and data["includes"].get("users"):
            for user in data["includes"]["users"]:
                authors[user["id"]] = {
                    "username": user.get("username", "unknown"),
                    "name": user.get("name", "Unknown"),
                }

        tweets = []
        for tweet in data["data"]:
            author_info = authors.get(
                tweet.get("author_id"), {"username": "unknown", "name": "Unknown"}
            )
            tweets.append(
                {
                    "id": tweet["id"],
                    "text": tweet.get("text", ""),
                    "author": author_info,
                    "created_at": tweet.get("created_at", ""),
                    "metrics": tweet.get("public_metrics", {}),
                    "url": f"https://twitter.com/{author_info['username']}/status/{tweet['id']}",
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": True,
                            "message": f"Retrieved {len(tweets)} tweets from home timeline.",
                            "count": len(tweets),
                            "tweets": tweets,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ]
        }

    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve home timeline (HTTP {e.response.status_code}): {error_detail}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "success": False,
                            "error": True,
                            "message": f"Failed to retrieve home timeline: {str(e)}",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                }
            ],
            "error": True,
        }


x_tools = [
    # OAuth 1.0a
    x_post_tweet,
    x_post_tweet_with_media,
    x_get_home_timeline,
    # OAuth 2.0
    x_get_tweet,
    x_get_my_tweets,
    x_search_recent_tweets,
]

def create_x_mcp_server():
    """X MCP server for Claude Code SDK"""
    return create_sdk_mcp_server(name="x", version="1.0.0", tools=x_tools)
