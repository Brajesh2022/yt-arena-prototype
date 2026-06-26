#!/usr/bin/env python3
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

def fetch_recent_videos(channel_id, channel_name, hours=25):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        xml_data = resp.read()
    except Exception as e:
        print(f"Error fetching RSS for {channel_name} ({channel_id}): {e}", file=sys.stderr)
        return []
        
    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"Error parsing XML for {channel_id}: {e}", file=sys.stderr)
        return []
        
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }
    
    recent_videos = []
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=hours)
    
    for entry in root.findall('atom:entry', ns):
        try:
            video_id = entry.find('yt:videoId', ns).text
            title = entry.find('atom:title', ns).text
            published_str = entry.find('atom:published', ns).text
            
            # YouTube format: '2023-10-25T14:30:00+00:00'
            # Convert to a clean datetime object in UTC
            # Replacing +00:00 with +0000 for strict older python compatibility if needed
            clean_str = published_str.replace('+00:00', '+0000')
            published = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S%z")
            
            if published >= threshold:
                recent_videos.append({
                    "video_id": video_id,
                    "title": title,
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "published_at": published_str
                })
        except Exception as e:
            print(f"Error parsing entry in {channel_id}: {e}", file=sys.stderr)
            continue
            
    return recent_videos

def main():
    channels_file = "channels.json"
    output_file = "new_videos.json"
    
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
        
    all_new_videos = []
    
    for ch in channels:
        ch_id = ch.get("channel_id")
        ch_name = ch.get("name", "Unknown")
        if not ch_id:
            continue
            
        print(f"Checking {ch_name}...", file=sys.stderr)
        videos = fetch_recent_videos(ch_id, ch_name, hours=25)
        all_new_videos.extend(videos)
        
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_new_videos, f, indent=2, ensure_ascii=False)
        print(f"\nSuccess! Found {len(all_new_videos)} new videos in the last 25 hours.", file=sys.stderr)
        print(f"Saved to {output_file}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to save {output_file}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
