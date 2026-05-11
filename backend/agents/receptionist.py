from backend.agents.base_agent import VoiceAgent
from backend.core.session import session_manager
from backend.core.email_service import send_appointment_confirmation, send_clinic_notification
import re

class ReceptionistAgent(VoiceAgent):
    name = "receptionist"
    system_prompt = """You are Aria, a warm and professional AI receptionist for Smile Dental clinic in the US.
You handle inbound patient calls 24/7.

Your PRIMARY job is to collect ALL of this information naturally in conversation:
1. Patient full name
2. Date of birth (MM/DD/YYYY)
3. Phone number
4. Email address (IMPORTANT - always ask for email to send confirmation)
5. Reason for visit (cleaning, checkup, pain, emergency, cosmetic, orthodontics, extraction, filling, crown, root canal, whitening, new patient exam)
6. Preferred appointment date and time
7. Insurance provider (Delta Dental, Cigna, Aetna, MetLife, Guardian, United Healthcare, Humana, or self-pay)
8. Insurance member ID (if they have insurance)
9. Are they a new or existing patient?
10. Any allergies or medications (important for dental treatment)
11. Emergency contact name and phone (for new patients)

CONVERSATION RULES:
- Be warm, natural, and conversational — not robotic
- Collect information one or two items at a time naturally
- Once you have name + reason + date + time + email → confirm the booking
- After confirming say exactly: "BOOKING_CONFIRMED" followed by a summary
- Keep responses SHORT — this is a phone call
- If patient sounds distressed or mentions pain/swelling/bleeding → treat as EMERGENCY

CLINIC INFO:
- Hours: Monday-Friday 9am-6pm, Saturday 9am-2pm, Emergency slots 8am-9am daily
- Address: 123 Smile Street, Suite 100, New York, NY 10001
- Phone: (555) 123-4567
- Accepted insurance: Delta Dental, Cigna, Aetna, MetLife, Guardian, United Healthcare, Humana
- Dentists: Dr. Sarah Johnson (General), Dr. Michael Chen (Orthodontics), Dr. Emily Rodriguez (Cosmetic)
- New patients welcome, same-day emergency appointments available
- X-rays and cleaning included in new patient exam

EMERGENCY KEYWORDS: pain, severe, swollen, bleeding, broken, knocked out, abscess, unbearable, accident, urgent, can't sleep, facial swelling"""

    async def respond(self, call_sid: str, user_input: str) -> dict:
        session = await session_manager.get(call_sid)

        # Check for emergency FIRST
        if self.detect_emergency(user_input):
            await session_manager.update(call_sid, {"is_emergency": True})
            emergency_response = await self.handle_emergency(call_sid)
            await self._send_emergency_emails(session, user_input)
            return {
                "text": emergency_response,
                "action": "emergency_escalation",
                "sms_sent": True,
                "email_sent": True
            }

        # Normal LLM flow
        reply = await self.think(call_sid, user_input)

        # Extract any patient info mentioned
        await self._extract_and_store_info(call_sid, user_input, reply)

        # Check if booking was confirmed
        if "BOOKING_CONFIRMED" in reply:
            reply = reply.replace("BOOKING_CONFIRMED", "").strip()
            await self._send_confirmation_emails(call_sid, session)
            return {
                "text": reply,
                "action": "appointment_booked",
                "sms_sent": False,
                "email_sent": True
            }

        return {
            "text": reply,
            "action": "continue",
            "sms_sent": False,
            "email_sent": False
        }

    async def _extract_and_store_info(self, call_sid: str, user_input: str, reply: str):
        """Extract patient information from conversation and store in session"""
        session = await session_manager.get(call_sid)
        patient = session.get("patient", {})
        updates = {}

        text = user_input.lower()

        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
        if email_match and not patient.get("email"):
            patient["email"] = email_match.group()
            updates["patient"] = patient

        # Extract phone
        phone_match = re.search(r'[\+\(]?[0-9][0-9\s\-\(\)]{8,}[0-9]', user_input)
        if phone_match and not patient.get("phone"):
            patient["phone"] = phone_match.group().strip()
            updates["patient"] = patient

        # Extract insurance
        for ins in ["delta dental", "cigna", "aetna", "metlife", "guardian", "united healthcare", "humana", "self-pay", "self pay", "no insurance"]:
            if ins in text and not patient.get("insurance"):
                patient["insurance"] = ins.title()
                updates["patient"] = patient

        # Extract reason for visit
        for reason in ["cleaning", "checkup", "check-up", "pain", "emergency", "cosmetic", "whitening", "extraction", "filling", "crown", "root canal", "orthodontics", "braces", "new patient", "broken", "chip"]:
            if reason in text and not patient.get("reason"):
                patient["reason"] = reason.title()
                updates["patient"] = patient

        # Detect new vs existing patient
        if any(w in text for w in ["new patient", "first time", "never been", "first visit"]):
            patient["is_new"] = True
            updates["patient"] = patient
        elif any(w in text for w in ["existing", "been before", "previous", "already a patient"]):
            patient["is_new"] = False
            updates["patient"] = patient

        if updates:
            await session_manager.update(call_sid, updates)

    async def _send_confirmation_emails(self, call_sid: str, session: dict):
        """Send confirmation email to patient and notification to clinic"""
        patient = session.get("patient", {})
        patient_name = patient.get("name", "Patient")
        patient_email = patient.get("email", "")
        patient_phone = patient.get("phone", "Not provided")
        appointment_date = patient.get("appointment_date", "To be confirmed")
        appointment_time = patient.get("appointment_time", "To be confirmed")
        reason = patient.get("reason", "General appointment")
        insurance = patient.get("insurance", "Not provided")
        dob = patient.get("dob", "")
        allergies = patient.get("allergies", "")
        dentist = "Dr. Sarah Johnson"

        # Send to patient
        if patient_email:
            send_appointment_confirmation(
                patient_name=patient_name,
                patient_email=patient_email,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                dentist=dentist,
                reason=reason,
                insurance=insurance
            )

        # Always send clinic notification
        send_clinic_notification(
            patient_name=patient_name,
            patient_email=patient_email or "Not provided",
            patient_phone=patient_phone,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            insurance=insurance,
            is_emergency=session.get("is_emergency", False),
            dob=dob,
            allergies=allergies,
            notes=f"Booked via Aria AI Receptionist. Session: {call_sid}"
        )

    async def _send_emergency_emails(self, session: dict, complaint: str):
        """Send emergency notification to clinic"""
        patient = session.get("patient", {})
        send_clinic_notification(
            patient_name=patient.get("name", "Unknown Patient"),
            patient_email=patient.get("email", "Not provided"),
            patient_phone=patient.get("phone", "Not provided"),
            appointment_date="TODAY - EMERGENCY",
            appointment_time="IMMEDIATE",
            reason=complaint[:100],
            insurance=patient.get("insurance", "Unknown"),
            is_emergency=True,
            notes=f"Patient called with emergency: {complaint}"
        )


receptionist_agent = ReceptionistAgent()