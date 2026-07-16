# ❄️ Fleet Snowfluff

A Discord bot powered by **Google Gemini** — conversational AI with per-channel memory, channel summarisation, and per-server configuration. Built with `discord.py` slash commands and a SQLAlchemy async ORM that can switch from SQLite to PostgreSQL by changing one env variable.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Commands](#commands)
  - [/chat](#chat-message)
  - [/clearchat](#clearchat)
  - [/summarize](#summarize-count)
  - [/ping](#ping)
  - [/help](#help)
  - [/config setchannel](#config-setchannel-channel)
  - [/config removechannel](#config-removechannel-channel)
  - [/config listchannels](#config-listchannels)
  - [/config setpersona](#config-setpersona-prompt)
  - [/config clearpersona](#config-clearpersona)
  - [/config showpersona](#config-showpersona)
- [Natural Chat Mode](#natural-chat-mode)
- [Conversation Memory](#conversation-memory)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Database & Migration](#database--migration)
- [Requirements](#requirements)

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/abdulhadi19306v10-oss/Fleet-Snowfluff.git
cd Fleet-Snowfluff

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fill in secrets
cp .env .env.local   # or just edit .env directly
#   DISCORD_TOKEN=your_discord_bot_token
#   GEMINI_API_KEY=your_gemini_api_key
#   DATABASE_URL=sqlite+aiosqlite:///fleet_snowfluff.db  ← default, already set

# 4. Run
python main.py
```

> **Bot permissions required:** `Send Messages`, `Read Message History`, `Use Slash Commands`, `Embed Links`  
> **Privileged intents required:** `Message Content`, `Server Members` (enable in the Discord Developer Portal)

Slash commands are synced globally on startup. Discord can take **up to 1 hour** to propagate them to all servers on first run.

---

## Commands

### `/chat <message>`

Chat directly with Fleet Snowfluff using Google Gemini. Every message and reply is stored in the database, so the bot remembers the last **20 conversation turns** in that channel as context for the next message.

| Parameter | Required | Description |
|---|---|---|
| `message` | ✅ | The message you want to send to the bot |

**Example:**
```
/chat What is the capital of France?
→ The capital of France is Paris.

/chat And what's it famous for?
→ Paris is famous for the Eiffel Tower, the Louvre, its cuisine...
```

The follow-up question works because Paris was already in the channel's conversation history.

---

### `/clearchat`

Wipes the bot's stored conversation memory for the **current channel only**. Other channels are unaffected. The bot reports how many messages were deleted. Response is ephemeral (only you see it).

**Use this when:**
- The conversation has gone off-track and you want a fresh start
- You want to change the subject without old context influencing replies

---

### `/summarize [count]`

Fetches the last `count` messages from the current channel and asks Gemini to produce a **bullet-point summary grouped by topic**, capturing key decisions, questions, and conclusions.

| Parameter | Required | Default | Range |
|---|---|---|---|
| `count` | ❌ | `50` | 2 – 200 |

The summary is returned as a Discord embed. If the transcript exceeds ~12,000 characters it is automatically truncated before being sent to Gemini.

**Example:**
```
/summarize 100
→ 📋 Summary of last 97 messages
  • Topic: Deployment — Team agreed to push Friday, John will handle infra
  • Topic: Design review — Logo rejected, new options due Wednesday
  • Topic: Bug reports — 3 open issues assigned to @dev-team
```

> Messages with no text content (images, embeds only) are skipped automatically.

---

### `/ping`

Reports the bot's current latency as an ephemeral embed (only you see the response).

| Metric | Description |
|---|---|
| **WebSocket** | Discord heartbeat latency — how fast the bot receives gateway events |
| **Round-trip** | Time from command send to response received |

**Example output:**
```
🏓 Pong!
WebSocket   42.3 ms
Round-trip  118.7 ms
```

---

### `/help`

Displays a full embed listing all available commands, grouped by category. Visible to everyone in the channel.

---

### `/config setchannel <channel>`

> 🔒 **Requires:** `Manage Server` permission

Adds a channel to the **natural chat** list. Once added, the bot will automatically respond to **every message** in that channel (not just `/chat` commands or @mentions) using the stored conversation context.

| Parameter | Required | Description |
|---|---|---|
| `channel` | ✅ | The text channel to enable |

```
/config setchannel #ai-chat
→ ✅ #ai-chat added.
```

---

### `/config removechannel <channel>`

> 🔒 **Requires:** `Manage Server` permission

Removes a channel from the natural chat list. The bot will stop auto-responding to regular messages there, but `/chat` and @mentions still work everywhere.

| Parameter | Required | Description |
|---|---|---|
| `channel` | ✅ | The text channel to disable |

---

### `/config listchannels`

> 🔒 **Requires:** `Manage Server` permission

Shows all channels currently configured for natural chat on this server. Response is ephemeral.

```
→ 📣 Natural-chat channels: #ai-chat, #general-bot
```

---

### `/config setpersona <prompt>`

> 🔒 **Requires:** `Manage Server` permission

Overrides the default Gemini system prompt with a **custom persona** for this server. This changes how the bot presents itself, its tone, its name, areas of expertise — anything a system prompt can control.

| Parameter | Required | Description |
|---|---|---|
| `prompt` | ✅ | The system prompt / persona instructions for Gemini |

**Example:**
```
/config setpersona You are Chip, a sarcastic but helpful tech support bot. Answer only tech questions.
```

The custom persona persists across bot restarts and applies to all Gemini calls on this server (`/chat`, natural chat, and `/summarize`).

---

### `/config clearpersona`

> 🔒 **Requires:** `Manage Server` permission

Resets the server's Gemini persona back to the default Fleet Snowfluff personality:

> *"You are Fleet Snowfluff, a friendly, helpful, and slightly whimsical Discord bot. Keep responses under 1800 characters unless the user asks for more."*

---

### `/config showpersona`

> 🔒 **Requires:** `Manage Server` permission

Displays the current active system prompt for this server in a code block. Shows `"Using the default Fleet Snowfluff persona."` if no custom prompt is set. Response is ephemeral.

---

## Natural Chat Mode

When a channel is added with `/config setchannel`, the bot enters **natural chat mode** for that channel — no slash command required. Just talk normally and the bot replies, with full conversation memory.

The bot also **always responds when @mentioned**, regardless of whether a channel is configured.

| Trigger | Requires setup | Works in DMs |
|---|---|---|
| `/chat` command | No | ✅ |
| @mention the bot | No | ✅ |
| Message in enabled channel | Yes (`/config setchannel`) | ❌ |

When @mentioned with no text (just a ping), the bot responds with a friendly prompt asking what you need.

---

## Conversation Memory

Memory is **per-channel**, not per-user. Every `/chat` call and natural-chat response stores both the user message and the bot reply in the database. The last **20 turns** (40 rows — 20 user + 20 model) are included as context in every Gemini call.

The database is automatically pruned to the most recent **40 rows per channel** after each interaction, so the database never grows unboundedly.

| Detail | Value |
|---|---|
| Context window (turns) | 20 |
| Max stored rows per channel | 40 |
| Scope | Per channel (not per user) |
| Persists across restarts | ✅ (stored in DB) |
| Cleared by | `/clearchat` |

---

## Error Handling

All Gemini API errors are caught and turned into user-friendly Discord messages. The bot never crashes silently.

| Error | Behaviour |
|---|---|
| **Rate limit (429)** | Exponential backoff: retries up to 3 times (1.5s → 3s → 6s), then sends a user-friendly message |
| **API error** | Caught, logged, error message shown to user |
| **Unexpected exception** | Caught, full traceback logged to console, generic error shown to user |
| **Missing permissions** | Slash command error handler returns a 🔒 ephemeral message |
| **Cooldown** | Returns remaining seconds in an ephemeral message |

---

## Configuration

All secrets and settings live in `.env` (never committed to git):

```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional — defaults to local SQLite if unset
DATABASE_URL=sqlite+aiosqlite:///fleet_snowfluff.db
```

### Gemini model settings (in `gemini_client.py`)

| Setting | Default | Description |
|---|---|---|
| `DEFAULT_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `temperature` | `0.7` | Response creativity (0 = deterministic, 1 = creative) |
| `top_p` | `0.95` | Nucleus sampling threshold |
| `max_output_tokens` | `1024` | Max tokens per reply |
| `MAX_RETRIES` | `3` | Retry attempts on rate limit |

---

## Project Structure

```
Fleet-Snowfluff/
├── main.py               # Bot init, cog loader, global error handler
├── gemini_client.py      # Gemini API wrapper — swap model/config here
├── requirements.txt
├── .env                  # Secrets (not in git)
├── .gitignore
│
├── cogs/
│   ├── chat.py           # /chat, /clearchat, @mention + channel listener
│   ├── summarize.py      # /summarize
│   └── utility.py        # /ping, /help, /config group
│
└── db/
    ├── models.py         # SQLAlchemy ORM models (ConversationHistory, GuildConfig)
    ├── session.py        # Async engine, session factory, all query helpers
    └── __init__.py       # Re-exports — cogs use `import db` unchanged
```

---

## Database & Migration

The bot uses **SQLAlchemy 2.0 async ORM** with `aiosqlite` as the default driver. Two tables are created automatically on first run:

### `conversation_history`
| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `channel_id` | BigInteger | Discord channel ID |
| `role` | String(10) | `'user'` or `'model'` |
| `content` | Text | Message content |
| `created_at` | DateTime | Row creation timestamp |

### `guild_config`
| Column | Type | Description |
|---|---|---|
| `guild_id` | BigInteger PK | Discord server ID |
| `enabled_channels` | JSON | List of channel IDs for natural chat |
| `system_prompt` | Text | Custom Gemini persona (nullable) |

### Switching to PostgreSQL

No code changes are required. Just update `DATABASE_URL` in `.env` and install the async driver:

```bash
pip install asyncpg

# In .env:
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fleet_snowfluff
```

SQLAlchemy handles the rest — `BigInteger` → `BIGINT`, `JSON` → native `JSONB`, all queries unchanged.

---

## Requirements

```
discord.py>=2.4.0
google-generativeai>=0.8.0
python-dotenv>=1.0.0
SQLAlchemy[asyncio]>=2.0.0
aiosqlite>=0.20.0
asyncpg>=0.30.0
```

Python **3.11+** required (uses `X | Y` union type hints).
