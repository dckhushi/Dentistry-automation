import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from backend.core.session import session_manager

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class VoiceAgent:
    name: str = "base"
    system_prompt: str = ""

    async def think(self, call_sid: str, user_input: str) -> str:
        await session_manager.append_turn(call_sid, "user", user_input)

        session = await session_manager.get(call_sid)
        history = session.get("history", [])

        messages = [{"role": "system", "content": self.build_system_prompt(session)}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        await session_manager.append_turn(call_sid, "assistant", reply)
        return reply

    def build_system_prompt(self, session: dict) -> str:
        patient = session.get("patient", {})
        clinic = session.get("clinic", {})
        base = self.system_prompt

        if patient:
            base += f"\n\nPatient on call: {patient.get('name', 'Unknown')}, DOB: {patient.get('dob', 'Unknown')}"
        if clinic:
            base += f"\nClinic: {clinic.get('name', 'Unknown')}, Hours: {clinic.get('hours', '9am-5pm Mon-Fri')}"

        return base

    async def handle_emergency(self, call_sid: str) -> str:
        session = await session_manager.get(call_sid)
        clinic = session.get("clinic", {})
        return (
            f"I can hear this is urgent. I'm booking you as an emergency case right now. "
            f"Please come directly to {clinic.get('address', 'our clinic')}. "
            f"I'm sending the address and directions to your phone right now. "
            f"Is there anything else you need before you come in?"
        )

    def detect_emergency(self, text: str) -> bool:
        emergency_keywords = [
            "pain", "severe", "emergency", "swollen", "bleeding",
            "broken", "knocked out", "abscess", "can't sleep",
            "unbearable", "accident", "urgent", "help"
        ]
        return any(keyword in text.lower() for keyword in emergency_keywords)