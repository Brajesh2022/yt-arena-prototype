#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone
import re

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def get_env_or_exit(var_name):
    val = os.environ.get(var_name)
    if not val:
        print(f"{RED}Error: {var_name} environment variable is not set.{RESET}")
        sys.exit(1)
    return val

def api_request(url, endpoint, key, payload):
    req = urllib.request.Request(f"{url.rstrip('/')}{endpoint}")
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('User-Agent', 'Mozilla/5.0 (compatible; YTRaterCLI/1.0)')
    data = json.dumps(payload).encode('utf-8')
    try:
        response = urllib.request.urlopen(req, data=data)
        return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"{RED}HTTP Error {e.code}: {e.read().decode('utf-8')}{RESET}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"{RED}URL Error: {e.reason}{RESET}")
        sys.exit(1)

def get_youtube_metadata(video_id):
    title = f"Video {video_id}"
    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    channel_id = None
    
    # 1. Try to get title, thumbnail, and fallback handle from oEmbed
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    req_oembed = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req_oembed, timeout=5)
        data = json.loads(resp.read().decode('utf-8'))
        title = data.get("title", title)
        thumbnail = data.get("thumbnail_url", thumbnail)
        
        author_url = data.get("author_url", "")
        if author_url:
            channel_id = author_url.rstrip('/').split('/')[-1]
    except Exception:
        pass


    if not channel_id:
        print(f"{YELLOW}Warning: Could not fetch YouTube metadata for {video_id}.{RESET}")
    
    return {
        "title": title,
        "thumbnail_url": thumbnail,
        "channel_id": channel_id
    }

def main():
    parser = argparse.ArgumentParser(description="YT Arena Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    filter_parser = subparsers.add_parser("filter", help="Filter out already rated videos")
    filter_parser.add_argument("ids", nargs="+", help="List of video IDs to check")

    rate_parser = subparsers.add_parser("rate", help="Submit a new video rating")
    rate_parser.add_argument("--video-id", required=True)
    rate_parser.add_argument("--channel-id", required=False, help="Optional. Will be auto-extracted if omitted.")
    rate_parser.add_argument("--quality", type=float, required=True, help="0 to 10")
    rate_parser.add_argument("--credibility", type=float, required=True, help="0 to 10")
    rate_parser.add_argument("--rationality", type=float, required=True, help="0 to 10")
    rate_parser.add_argument("--neutrality", type=float, required=True, help="-10 to 10")
    rate_parser.add_argument("--summary", required=True)
    
    rate_parser.add_argument("--title", help="Override video title")
    rate_parser.add_argument("--thumbnail", help="Override thumbnail URL")
    rate_parser.add_argument("--published-at", help="Override published_at (ISO8601)")

    transcript_parser = subparsers.add_parser("transcript", help="Download and simplify transcript for a video")
    transcript_parser.add_argument("--video-id", required=True)

    args = parser.parse_args()
    args = parser.parse_args()

    if args.command == "filter":
        url = get_env_or_exit("YT_ARENA_URL")
        key = get_env_or_exit("YT_ARENA_KEY")
        unrated = api_request(url, "/api/filter-unrated", key, {"ids": args.ids})
        print(json.dumps(unrated))

    elif args.command == "rate":
        url = get_env_or_exit("YT_ARENA_URL")
        key = get_env_or_exit("YT_ARENA_KEY")
        neutrality_score = 10 - abs(args.neutrality)
        composite = (
            args.quality * 0.30 +
            args.credibility * 0.30 +
            args.rationality * 0.25 +
            neutrality_score * 0.15
        )
        if args.neutrality <= -3:
            label = "LEFT"
        elif args.neutrality >= 3:
            label = "RIGHT"
        else:
            label = "NEUTRAL"

        metadata = get_youtube_metadata(args.video_id)
        
        title = args.title if args.title else metadata["title"]
        thumbnail = args.thumbnail if args.thumbnail else metadata["thumbnail_url"]
        published_at = args.published_at if args.published_at else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "yt_video_id": args.video_id,
            "channel_id": args.channel_id,
            "title": title,
            "thumbnail_url": thumbnail,
            "published_at": published_at,
            "quality": args.quality,
            "credibility": args.credibility,
            "rationality": args.rationality,
            "neutrality": args.neutrality,
            "neutrality_label": label,
            "composite": composite,
            "summary": args.summary
        }
        
        print(f"Submitting rating for {title}...")
        result = api_request(url, "/api/rate-video", key, payload)
        if result.get("success"):
            print(f"{GREEN}Successfully submitted rating for {args.video_id}!{RESET}")
            print(f"Calculated Composite: {composite:.2f}")
            print(f"Calculated Label: {label}")
        else:
            print(f"{RED}Failed to submit: {result}{RESET}")
    elif args.command == "transcript":
        url = os.environ.get("YT_ARENA_URL")
        key = os.environ.get("YT_ARENA_KEY")
        
        if not url or not key:
            print(f"{YELLOW}Warning: YT_ARENA_URL or YT_ARENA_KEY not set. Cannot fetch transcript via Cloudflare API. Using empty transcript fallback.{RESET}")
            filename = f"transcript_{args.video_id}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("[Transcript blocked. YT_ARENA_URL/KEY not configured. Rate this video purely based on Title, Channel, and Metadata]")
            sys.exit(0)
            
        print(f"Fetching transcript for {args.video_id} via Cloudflare API...")
        try:
            req = urllib.request.Request(f"{url.rstrip('/')}/api/transcript?videoId={args.video_id}")
            req.add_header('Authorization', f'Bearer {key}')
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; YTRaterCLI/1.0)')
            
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode('utf-8'))
            
            if data.get("success"):
                full_text = data.get("transcript", "")
                filename = f"transcript_{args.video_id}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                print(f"{GREEN}Success! Transcript saved to {filename}{RESET}")
            else:
                raise Exception(data.get("error", "Unknown API Error"))
                
        except Exception as e:
            print(f"{YELLOW}Warning: Failed to fetch transcript via API ({e}). Using empty transcript fallback.{RESET}")
            filename = f"transcript_{args.video_id}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("[Transcript blocked by YouTube IP limits. Rate this video purely based on Title, Channel, and Metadata]")
            sys.exit(0)

if __name__ == "__main__":
    main()
