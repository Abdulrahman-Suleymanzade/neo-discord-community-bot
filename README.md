# Neo Discord Community Bot

Production-ready Discord community management bot built with Python, featuring XP leveling, slash commands, leaderboards, role rewards readiness, persistent data storage, and scalable cloud deployment.

## Features

- XP leveling system
- Anti-farm XP cooldown
- `/rank` slash command
- `/leaderboard` slash command
- SQLite persistent storage
- Discord embeds
- Render cloud deployment ready

## Tech Stack

- Python
- discord.py
- SQLite
- Render
- Discord Developer Portal

## Environment Variables

Create this variable in Render:

```env
DISCORD_TOKEN=your_discord_bot_token
```

## Run Locally

```bash
pip install -r requirements.txt
python bot.py
```

## Deployment

This project includes `render.yaml` for deployment as a Render background worker.
