"""gemini_client.py — Gemini API wrapper for Fleet Snowfluff."""

import asyncio
import logging
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger("fleet_snowfluff.gemini")

DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_SYSTEM_PROMPT = (
    "You are Fleet Snowfluff, a friendly, helpful, and slightly whimsical Discord bot. "
    "Keep responses under 1800 characters unless the user asks for more."
)
MAX_RETRIES = 3


def configure(api_key: str) -> None:
    genai.configure(api_key=api_key)


def _model(system_prompt: str | None = None) -> genai.GenerativeModel:
    # ponytail: inline instead of separate build helper + config object
    return genai.GenerativeModel(
        model_name=DEFAULT_MODEL,
        generation_config={"temperature": 0.7, "top_p": 0.95, "max_output_tokens": 1024},
        system_instruction=system_prompt or DEFAULT_SYSTEM_PROMPT,
    )


async def _call(fn, *args, **kwargs):
    # ponytail: run_in_executor wraps any blocking call — no need for a named decorator
    return await asyncio.get_running_loop().run_in_executor(None, lambda: fn(*args, **kwargs))


async def _with_retry(fn):
    """Run async callable `fn` up to MAX_RETRIES times, backing off on 429."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await fn()
        except google_exceptions.ResourceExhausted:
            if attempt == MAX_RETRIES:
                return "⚠️ Gemini is rate-limited right now. Please wait a moment and try again."
            await asyncio.sleep(1.5 * 2 ** (attempt - 1))
        except google_exceptions.GoogleAPICallError as e:
            logger.error("Gemini API error: %s", e)
            return f"⚠️ Gemini API error: {e}"
        except Exception as e:
            logger.exception("Unexpected Gemini error: %s", e)
            return "⚠️ Something went wrong contacting Gemini. Please try again."


async def chat(user_message: str, history: list[dict] | None = None, system_prompt: str | None = None) -> str:
    sdk_history = [{"role": m["role"], "parts": [m["content"]]} for m in (history or [])]

    async def _do():
        session = _model(system_prompt).start_chat(history=sdk_history)
        return (await _call(session.send_message, user_message)).text.strip()

    return await _with_retry(_do)


async def summarize(text: str, system_prompt: str | None = None) -> str:
    prompt = (
        "Summarise this Discord conversation with bullet points grouped by topic. "
        f"Be concise but capture key decisions and conclusions.\n\n{text}"
    )

    async def _do():
        return (await _call(_model(system_prompt).generate_content, prompt)).text.strip()

    return await _with_retry(_do)
