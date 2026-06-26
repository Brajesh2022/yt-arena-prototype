#!/usr/bin/env bash
set -e

source ~/.cloudflare/cloudflare.env
ACCOUNT_ID=$CLOUDFLARE_ACCOUNT_ID
TOKEN=$CLOUDFLARE_API_TOKEN
PROJECT_NAME="yt-arena-prototype"

cd ~/yt-arena-prototype
rm -f project.zip
cd public && zip -r ../project.zip * && cd ..
zip -r project.zip functions package.json
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects/$PROJECT_NAME/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@project.zip" > deploy_result.json

cat deploy_result.json
