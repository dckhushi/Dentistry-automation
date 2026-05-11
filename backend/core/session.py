import json
import os
from dotenv import load_dotenv

load_dotenv()

from upstash_redis.asyncio import Redis

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        url = os.getenv("UPSTASH_REDIS_URL")
        token = os.getenv("UPSTASH_REDIS_TOKEN")
        _redis_client = Redis(url=url, token=token)
    return _redis_client

class SessionManager:
    TTL = 14400

    async def create(self, call_sid: str, data: dict):
        await get_redis().setex(
            f"call:{call_sid}",
            self.TTL,
            json.dumps(data)
        )

    async def get(self, call_sid: str) -> dict:
        try:
            raw = await get_redis().get(f"call:{call_sid}")
            if raw:
                if isinstance(raw, dict):
                    return raw
                return json.loads(raw)
        except Exception as e:
            print(f"Redis get error: {e}")
        return {}

    async def update(self, call_sid: str, data: dict):
        existing = await self.get(call_sid)
        existing.update(data)
        await get_redis().setex(
            f"call:{call_sid}",
            self.TTL,
            json.dumps(existing)
        )

    async def delete(self, call_sid: str):
        await get_redis().delete(f"call:{call_sid}")

    async def append_turn(self, call_sid: str, role: str, content: str):
        session = await self.get(call_sid)
        history = session.get("history", [])
        history.append({"role": role, "content": content})
        if len(history) > 8:
            history = history[-8:]
        session["history"] = history
        await get_redis().setex(
            f"call:{call_sid}",
            self.TTL,
            json.dumps(session)
        )

session_manager = SessionManager()