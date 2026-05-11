from supabase import create_client, Client
from backend.core.config import settings

_db_client: Client = None

def get_db() -> Client:
    """
    Returns Supabase client.
    Singleton pattern - one client for the whole app.
    """
    global _db_client
    if _db_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase credentials missing in .env")
        _db_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _db_client


async def log_call(call_sid: str, clinic_id: str, agent_type: str, caller_number: str) -> str:
    """Insert a new call record and return the call ID"""
    try:
        db = get_db()
        result = db.table("calls").insert({
            "twilio_call_sid": call_sid,
            "clinic_id": clinic_id,
            "agent_type": agent_type,
            "caller_number": caller_number,
            "status": "active"
        }).execute()
        return result.data[0]["id"]
    except Exception as e:
        print(f"Call log error: {e}")
        return None


async def update_call(call_sid: str, updates: dict):
    """Update call record by twilio_call_sid"""
    try:
        db = get_db()
        db.table("calls")\
            .update(updates)\
            .eq("twilio_call_sid", call_sid)\
            .execute()
    except Exception as e:
        print(f"Call update error: {e}")


async def save_transcript(call_id: str, full_text: str, structured_output: dict):
    """Save call transcript and structured extraction"""
    try:
        db = get_db()
        db.table("call_transcripts").insert({
            "call_id": call_id,
            "full_text": full_text,
            "structured_output": structured_output
        }).execute()
    except Exception as e:
        print(f"Transcript save error: {e}")


async def save_eligibility(call_id: str, patient_id: str, payer_id: str, data: dict):
    """Save insurance eligibility results"""
    try:
        db = get_db()
        db.table("eligibility_results").insert({
            "call_id": call_id,
            "patient_id": patient_id,
            "payer_id": payer_id,
            **data
        }).execute()
    except Exception as e:
        print(f"Eligibility save error: {e}")


async def get_ivr_paths(payer_id: str) -> list:
    """Get all learned IVR paths for a payer"""
    try:
        db = get_db()
        result = db.table("payer_ivr_paths")\
            .select("*")\
            .eq("payer_id", payer_id)\
            .order("confidence", desc=True)\
            .execute()
        return result.data
    except Exception as e:
        print(f"IVR path fetch error: {e}")
        return []


async def get_recent_calls(limit: int = 20) -> list:
    """Get recent calls for dashboard"""
    try:
        db = get_db()
        result = db.table("calls")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    except Exception as e:
        print(f"Recent calls fetch error: {e}")
        return []


async def audit(table_name: str, row_id: str, action: str, clinic_id: str = None):
    """HIPAA audit log - append only"""
    try:
        db = get_db()
        db.table("audit_log").insert({
            "table_name": table_name,
            "row_id": row_id,
            "action": action,
            "clinic_id": clinic_id
        }).execute()
    except Exception as e:
        print(f"Audit log error: {e}")