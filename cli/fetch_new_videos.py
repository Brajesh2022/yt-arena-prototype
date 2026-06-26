#!/usr/bin/env python3
import sys
import json
import os
import subprocess
from datetime import datetime, timezone

def resolve_handle_to_id(handle):
    import urllib.request
    import re
    url = f"https://www.youtube.com/{handle}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        match = re.search(r'<meta itemprop="identifier" content="(UC[^"]+)">', html)
        if match:
            return match.group(1)
    except Exception:
        pass
    return handle

def fetch_latest_videos(channel_id, channel_name):
    """
    Fetches the latest 3 videos using yt-dlp flat-playlist.
    This completely bypasses YouTube RSS and its 404 blocks.
    """
    if channel_id.startswith('@'):
        print(f"Resolving handle {channel_id} to Channel ID...", file=sys.stderr)
        channel_id = resolve_handle_to_id(channel_id)

    url = f"https://www.youtube.com/channel/{channel_id}"
    
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--playlist-end", "3", "--print", "%(id)s|%(title)s", url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0:
            print(f"Error fetching videos for {channel_name} ({channel_id}): {result.stderr}", file=sys.stderr)
            return []
            
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line or '|' not in line:
                continue
            vid_id, title = line.split('|', 1)
            videos.append({
                "video_id": vid_id.strip(),
                "title": title.strip(),
                "channel_id": channel_id,
                "channel_name": channel_name,
                "published_at": datetime.now(timezone.utc).isoformat()  # Extracted today
            })
        return videos
    except Exception as e:
        print(f"Error fetching videos for {channel_name} ({channel_id}): {e}", file=sys.stderr)
        return []

def main():
    channels_file = "channels.json"
    output_file = "new_videos.json"
    state_file = "rated_videos_state.json"
    
    if len(sys.argv) > 1:
        channels_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception as e:
        print(f"Failed to load {channels_file}: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Load state (previously processed videos)
    processed_videos = []
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                processed_videos = json.load(f)
        except Exception:
            pass
            
    all_new_videos = []
    
    for ch in channels:
        ch_id = ch.get("channel_id")
        ch_name = ch.get("name", "Unknown")
        if not ch_id:
            continue
            
        print(f"Checking {ch_name}...", file=sys.stderr)
        latest_videos = fetch_latest_videos(ch_id, ch_name)
        
        for video in latest_videos:
            if video["video_id"] not in processed_videos:
                all_new_videos.append(video)
                processed_videos.append(video["video_id"]) # Mark as processed
        
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_new_videos, f, indent=2, ensure_ascii=False)
            
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(processed_videos, f, indent=2)
            
        print(f"\nSuccess! Found {len(all_new_videos)} new unprocessed videos.", file=sys.stderr)
        print(f"Saved to {output_file}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to save results: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
