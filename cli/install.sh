#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
pip install --upgrade youtube-transcript-api
echo "Installing yt-rater CLI..."

SCRIPT_URL="https://raw.githubusercontent.com/Brajesh2022/yt-arena-prototype/master/cli/yt_rater.py"
INSTALL_DIR="/usr/local/bin"

if [ -d "/data/data/com.termux/files/usr/bin" ]; then
    TARGET="/data/data/com.termux/files/usr/bin/yt-rater"
elif [ -w "$INSTALL_DIR" ]; then
    TARGET="$INSTALL_DIR/yt-rater"
else
    TARGET="$HOME/.local/bin/yt-rater"
    mkdir -p "$HOME/.local/bin"
fi

curl -sL "$SCRIPT_URL" -o "$TARGET"
chmod +x "$TARGET"

echo -e "\033[92myt-rater CLI installed to $TARGET!\033[0m"
echo "Please set YT_ARENA_URL and YT_ARENA_KEY environment variables before using."
