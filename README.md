# 🌌 Fleet Snowfluff (Aemeath)

A Discord bot powered by **Google Gemini**, bringing the digital ghost **Aemeath** (also known by her musical persona, Fleet Snowfluff) from *Wuthering Waves* to life in your server. She features conversational AI with per-channel memory, channel summarisation, Aemeath GIF loops, and per-server configuration. Built with `discord.py` slash commands and a SQLAlchemy async ORM.

> *"Can you hear my frequencies tuning with yours? Let's soar through the starlight together!"*

---

## 🎵 Table of Contents

- [Quick Start](#quick-start)
- [Commands](#commands)
- [Natural Chat Mode](#natural-chat-mode)
- [Conversation Memory](#conversation-memory)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Database & Migration](#database--migration)

---

## 🌟 Quick Start

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

# 4. Run the Exostrider Synchronist
python main.py
```

> **Bot permissions required:** `Send Messages`, `Read Message History`, `Use Slash Commands`, `Embed Links`  
> **Privileged intents required:** `Message Content`, `Server Members`

---

## ✨ Commands

### 💬 `/chat <message>`
*(Restricted to Mods/Master User)*
Chat directly with Aemeath! Every message and reply is stored in the database, allowing her to remember the last **20 conversation turns** in that channel as context.

### 🧹 `/clearchat`
*(Restricted to Mods/Master User)*
Wipes Aemeath's stored conversation memory for the **current channel only**. 

### 📋 `/summarize [count]`
*(Restricted to Mods/Master User)*
Fetches the last `count` messages from the current channel and asks Aemeath to produce a **bullet-point summary** (max 2-3 sentences), capturing exactly who said what and what was discussed. 

### 🏓 `/ping`
*(Restricted to Mods/Master User)*
Reports the bot's current latency (WebSocket and Round-trip).

### 🛠️ `/purge`
*(Restricted to Mods/Master User)*
Deletes all of Aemeath's own messages in the current channel sent within the last 10 minutes.

### 📖 `/help`
*(Restricted to Mods/Master User)*
Displays a full embed listing all available commands.

---

### ⚙️ Config Group (Admins)

- **`/config setchannel <channel>`**: Enables natural chat in a specific channel. She will automatically tune her frequencies to read and respond to every message there.
- **`/config removechannel <channel>`**: Disables natural chat in that channel.
- **`/config listchannels`**: Lists all active natural-chat channels.
- **`/config setpersona <prompt>`**: Overrides her default Wuthering Waves persona with a custom one for the server.
- **`/config clearpersona`**: Restores Aemeath to her true digital ghost self!
- **`/config showpersona`**: Displays the active persona prompt.

---

### 🖼️ Aemeath GIFs

- **`/aemeath addgif <url>`**: Adds a new Aemeath GIF to her global pool (checks for duplicates!).
- **`/aemeath setchannel <channel>`**: Enables the auto-GIF Mechascout loop in a channel.
- **`/aemeath removechannel <channel>`**: Disables the auto-GIF loop in a channel.
- **`/aemeath setinterval <minutes>`**: Sets how often (in minutes) Aemeath drops a random GIF in the enabled channels.

---

## 🎶 Natural Chat Mode

When a channel is added with `/config setchannel`, Aemeath enters **natural chat mode** for that channel — no slash command required. Just talk normally and she replies.

She will also **always respond when @mentioned**, regardless of whether a channel is configured. If you ping her without text, she will respond with a friendly greeting!

> **Security Note:** Chat capabilities (`/chat`, `@mentions`, and natural chat) are strictly locked to Server Moderators (`Manage Server`/`Manage Messages`/`Administrator`) or the global Master User.

---

## 🧠 Conversation Memory (Frequencies)

Memory is **per-channel**, not per-user. The last **20 turns** (40 rows — 20 user + 20 model) are included as context in every Gemini call so she never loses her tune.

The database is automatically pruned to the most recent **40 rows per channel** after each interaction, keeping her frequencies clean and optimized.

---

## ⚙️ Configuration

All secrets and settings live in `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite+aiosqlite:///fleet_snowfluff.db
```

---

## 🗂️ Project Structure

```
Fleet-Snowfluff/
├── main.py               # Bot init, cog loader
├── gemini_client.py      # Gemini API wrapper & Aemeath Persona
├── utils.py              # Permissions & guards
├── cogs/
│   ├── chat.py           # /chat, /clearchat, mentions
│   ├── summarize.py      # /summarize
│   ├── utility.py        # /ping, /help, /config, /purge
│   └── aemeath.py        # Auto-GIF loop and GIF commands
└── db/
    ├── models.py         # SQLAlchemy ORM models
    └── session.py        # Async engine & queries
```

---

## 💾 Database & Migration

The bot uses **SQLAlchemy 2.0 async ORM** with `aiosqlite`. Tables are created automatically on first run.

To switch to PostgreSQL, just update `DATABASE_URL` in `.env` and install the async driver:
```bash
pip install asyncpg
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fleet_snowfluff
```

---

*“May the starlight guide your way, Rover!”* ❄️✨
