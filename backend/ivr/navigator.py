import json
import os
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from groq import Groq
from backend.core.database import get_db

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class IVRNavigator:
    def __init__(self):
        self.active_sessions = {}

    async def navigate(self, call_sid: str, payer_id: str, task_type: str, audio_text: str) -> dict:
        known_path = await self.load_path(payer_id, task_type)
        if known_path and known_path["confidence"] > 0.7:
            return await self.replay_path(call_sid, known_path, audio_text)
        else:
            return await self.explore(call_sid, payer_id, task_type, audio_text)

    async def load_path(self, payer_id: str, task_type: str) -> dict:
        try:
            db = get_db()
            result = db.table("payer_ivr_paths")\
                .select("*")\
                .eq("payer_id", payer_id)\
                .eq("task_type", task_type)\
                .order("confidence", desc=True)\
                .limit(1)\
                .execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            print(f"Path load error: {e}")
        return None

    async def replay_path(self, call_sid: str, path_record: dict, current_audio: str) -> dict:
        path = path_record["path"]
        session = self.active_sessions.get(call_sid, {"step": 0})
        current_step = session.get("step", 0)

        if current_step >= len(path):
            return {"action": "live_agent_mode", "dtmf": None}

        step = path[current_step]
        if self._audio_matches(current_audio, step.get("prompt", "")):
            self.active_sessions[call_sid] = {"step": current_step + 1}
            return {
                "action": "dtmf",
                "dtmf": step["key"],
                "delay_ms": step.get("delay_ms", 1200),
                "cost": "zero_llm"
            }
        else:
            return await self.explore(call_sid, path_record["payer_id"], path_record["task_type"], current_audio)

    async def explore(self, call_sid: str, payer_id: str, task_type: str, audio_text: str) -> dict:
        prompt = f"""You are navigating an insurance company IVR phone system.
Payer: {payer_id}
Task: {task_type}
Current IVR audio: "{audio_text}"

What DTMF digit or action should be taken to reach {task_type}?
Respond in JSON only, no markdown:
{{"action": "dtmf", "digit": "2", "reasoning": "option 2 is for eligibility"}}"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )

        try:
            result = json.loads(response.choices[0].message.content.strip())
        except:
            result = {"action": "wait", "seconds": 2, "reasoning": "parse error"}

        await self.record_step(call_sid, payer_id, task_type, audio_text, result)
        return result

    async def record_step(self, call_sid: str, payer_id: str, task_type: str, prompt: str, action: dict):
        if call_sid not in self.active_sessions:
            self.active_sessions[call_sid] = {"steps": [], "payer_id": payer_id, "task_type": task_type}
        self.active_sessions[call_sid].setdefault("steps", []).append({
            "prompt": prompt,
            "key": action.get("digit", action.get("text", "")),
            "delay_ms": 1200,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def record_outcome(self, call_sid: str, success: bool, duration_s: int):
        session = self.active_sessions.get(call_sid)
        if not session or not session.get("steps"):
            return

        payer_id = session.get("payer_id")
        task_type = session.get("task_type")
        steps = session.get("steps", [])

        if not success:
            await self._decrement_confidence(payer_id, task_type)
            return

        try:
            db = get_db()
            existing = db.table("payer_ivr_paths")\
                .select("*")\
                .eq("payer_id", payer_id)\
                .eq("task_type", task_type)\
                .execute()

            if existing.data:
                record = existing.data[0]
                new_confidence = min(0.99, record["confidence"] + 0.1)
                db.table("payer_ivr_paths").update({
                    "path": steps,
                    "confidence": new_confidence,
                    "success_count": record["success_count"] + 1,
                    "avg_duration_s": int((record["avg_duration_s"] + duration_s) / 2)
                }).eq("payer_id", payer_id).eq("task_type", task_type).execute()
            else:
                db.table("payer_ivr_paths").insert({
                    "payer_id": payer_id,
                    "task_type": task_type,
                    "path": steps,
                    "confidence": 0.3,
                    "success_count": 1,
                    "avg_duration_s": duration_s
                }).execute()
        except Exception as e:
            print(f"Path recording error: {e}")

        if call_sid in self.active_sessions:
            del self.active_sessions[call_sid]

    async def _decrement_confidence(self, payer_id: str, task_type: str):
        try:
            db = get_db()
            existing = db.table("payer_ivr_paths")\
                .select("*")\
                .eq("payer_id", payer_id)\
                .eq("task_type", task_type)\
                .execute()
            if existing.data:
                new_confidence = max(0.1, existing.data[0]["confidence"] - 0.15)
                db.table("payer_ivr_paths").update({
                    "confidence": new_confidence
                }).eq("payer_id", payer_id).eq("task_type", task_type).execute()
        except Exception as e:
            print(f"Confidence decrement error: {e}")

    def _audio_matches(self, audio: str, expected_prompt: str) -> bool:
        if not expected_prompt:
            return True
        keywords = expected_prompt.lower().split()
        matches = sum(1 for word in keywords if word in audio.lower())
        return matches / max(len(keywords), 1) > 0.5


ivr_navigator = IVRNavigator()