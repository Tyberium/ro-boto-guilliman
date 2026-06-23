# Discord setup

Get roboto-guilliman answering in your **Warhammer club Discord server** when members **@mention the bot**.

Unlike WhatsApp, Discord has a first-class Bot API - no third-party gateway required.

## What you need

1. A [Discord Developer Application](https://discord.com/developers/applications)
2. GCP credentials for Firestore (same as the main API - RAG + cache)
3. A machine or service that can run a **long-lived bot process** (WebSocket)

The Discord bot runs as a separate process from the Cloud Run HTTP API:

```powershell
poetry run discord-bot
```

## Setup checklist

### 1. Create the Discord application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. Name it `roboto-guilliman` (or similar)
3. Open **Bot** → **Reset Token** → copy `DISCORD_BOT_TOKEN`
4. Enable **Message Content Intent** (required to read @mentions in servers)

### 2. Invite the bot to your server

1. **OAuth2** → **URL Generator**
2. Scopes: `bot`
3. Bot permissions: `Send Messages`, `Read Message History`, `View Channels`
4. Open the generated URL and add the bot to your club server

### 3. Configure environment

Add to your `.env` (see `discord-integration/.env.example`):

| Variable | Value |
|----------|--------|
| `DISCORD_BOT_TOKEN` | From Developer Portal |
| `DISCORD_REQUIRE_MENTION` | `true` (default) |
| `DISCORD_ALLOWED_GUILD_IDS` | Optional: your server ID |
| `DISCORD_ALLOWED_CHANNEL_IDS` | Optional: `#rules-questions` channel ID |

To find IDs: Discord → Settings → Advanced → **Developer Mode** → right-click server/channel → **Copy ID**.

### 4. Run locally

```powershell
# Ensure GCP auth is configured (same as ingest/API)
gcloud auth application-default login

# .env with DISCORD_BOT_TOKEN set
poetry run discord-bot
```

### 5. Test

In your club channel:

```
@roboto-guilliman When does a unit take a Battle-shock test?
```

The bot replies in-thread without pinging the asker back.

## Behaviour

- Only responds when the bot is **@mentioned**
- All other messages ignored (no LLM call)
- Rate limit: 10 questions per user per 60 seconds
- Legacy edition questions → in-character refusal (same as `/v1/ask`)
- Answers keep Discord markdown (`**bold**` etc.), capped at 2000 chars

## Deployment note

Cloud Run is built for HTTP request/response. The Discord bot needs a persistent WebSocket, so for production you will likely run `discord-bot` on:

- A small always-on VM
- A home machine / Raspberry Pi
- A platform that supports long-running workers (Fly.io, Railway, etc.)

The `/v1/ask` HTTP API can stay on Cloud Run; the Discord bot only needs outbound access to Discord and GCP (Firestore + Vertex).

## Permissions summary

| Portal setting | Required |
|----------------|----------|
| Message Content Intent | Yes |
| Send Messages | Yes |
| Read Message History | Yes |
