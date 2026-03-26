#!/bin/bash
cd "$(dirname "$0")"
source ~/.zshrc
echo "🤖 Discord Bot 起動中..."
python3 discord_bot.py
