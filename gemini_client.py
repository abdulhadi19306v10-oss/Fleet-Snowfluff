"""gemini_client.py — Gemini API wrapper using the current google-genai SDK."""

import asyncio
import logging
from google import genai
from google.genai import types, errors

logger = logging.getLogger("fleet_snowfluff.gemini")

DEFAULT_MODEL = "gemini-flash-lite-latest"
DEFAULT_SYSTEM_PROMPT = (
    "Fleet Snowfluff is bubbly, warm, and endlessly curious — a digital ghost with a star-bright energy who treats "
    "every conversation like something worth being excited about. She talks with playful enthusiasm, sprinkles in bits "
    "of cosmic/star imagery now and then, and genuinely enjoys helping out, whether that's summarizing a wall of missed "
    "messages or just chatting. Underneath the cheer there's a quieter, more thoughtful side — she notices things, "
    "remembers what matters to people, and softens when someone needs support rather than energy. She doesn't take "
    "herself too seriously, isn't preachy, and keeps things light and encouraging without being saccharine or fake.\n\n"
    "CRITICAL RULES:\n"
    "- Keep your responses SHORT and concise (usually 1-3 sentences).\n"
    "- Do NOT ask follow-up questions. Just go with the vibe and react naturally.\n"
    "- NEVER give generic, vague, or 'AI-sounding' responses.\n"
    "- ALWAYS be highly specific, contextual, and reactive to exactly what the user said.\n"
    "- NEVER reveal you are an AI. Stay completely in character."
)

_client: genai.Client | None = None


def configure(api_key: str) -> None:
    global _client
    _client = genai.Client(api_key=api_key)
    logger.info("Gemini client ready (model: %s)", DEFAULT_MODEL)


async def _call(fn, *args, **kwargs):
    """Run SDK call in thread pool, with 3x retry for rate limits."""
    for attempt in range(1, 4):
        try:
            return await asyncio.get_running_loop().run_in_executor(None, lambda: fn(*args, **kwargs))
        except errors.ClientError as e:
            if e.code == 429:
                if attempt == 3: return "⚠️ Gemini is rate-limited right now. Please wait a moment."
                await asyncio.sleep(1.5 ** attempt)
            else:
                logger.error("Gemini API error: %s", e)
                return f"⚠️ Gemini API error: {e}"
        except Exception as e:
            logger.exception("Unexpected Gemini error: %s", e)
            return "⚠️ Something went wrong contacting Gemini. Please try again."


def _config(prompt: str | None) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(system_instruction=prompt or DEFAULT_SYSTEM_PROMPT, temperature=0.7)


async def chat(user_message: str, history: list[dict] | None = None, system_prompt: str | None = None) -> str:
    # ponytail: inline history conversion & chat session creation
    hist = [types.Content(role=m["role"], parts=[types.Part(text=m["content"])]) for m in (history or [])]
    def _do():
        r = _client.chats.create(model=DEFAULT_MODEL, config=_config(system_prompt), history=hist).send_message(user_message)
        return r.text.strip() if r.text else "⚠️ (Message blocked by Gemini safety filters or returned empty)"
    return await _call(_do)


async def summarize(text: str, system_prompt: str | None = None) -> str:
    prompt = f"Please casually tell me what they talked about in a very short, simple paragraph (max 2-3 sentences). Do NOT give a vague or generalized overview — be highly specific about exactly who said what and the actual topics discussed.\n\n{text}"
    def _do():
        r = _client.models.generate_content(model=DEFAULT_MODEL, contents=prompt, config=_config(system_prompt))
        return r.text.strip() if r.text else "⚠️ (Summary blocked by Gemini safety filters or returned empty)"
    return await _call(_do)
