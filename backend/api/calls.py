from fastapi import APIRouter, Request
from backend.core.database import (
    get_recent_calls, get_ivr_paths,
    log_call, update_call, save_transcript
)
from backend.agents.receptionist import receptionist_agent
from backend.ivr.navigator import ivr_navigator

router = APIRouter(prefix="/api", tags=["calls"])


# ─── Dashboard APIs ──────────────────────────────────────────────────────────

@router.get("/calls")
async def get_calls():
    """Get recent calls for dashboard"""
    calls = await get_recent_calls(limit=50)
    return {"calls": calls, "total": len(calls)}


@router.get("/ivr/paths/{payer_id}")
async def get_payer_paths(payer_id: str):
    """Get learned IVR paths for a payer"""
    paths = await get_ivr_paths(payer_id)
    return {
        "payer_id": payer_id,
        "paths": paths,
        "total": len(paths)
    }


@router.get("/ivr/paths")
async def get_all_paths():
    """Get all learned IVR paths across all payers"""
    payers = ["aetna_dental", "cigna_dental", "delta_dental", "metlife_dental", "guardian_dental"]
    all_paths = []
    for payer in payers:
        paths = await get_ivr_paths(payer)
        all_paths.extend(paths)
    return {
        "paths": all_paths,
        "total": len(all_paths)
    }


@router.get("/stats")
async def get_stats():
    """Get platform statistics for dashboard"""
    from backend.core.database import get_db
    db = get_db()

    try:
        total_calls = db.table("calls").select("id", count="exact").execute()
        emergency_calls = db.table("calls").select("id", count="exact").eq("is_emergency", True).execute()
        ivr_paths = db.table("payer_ivr_paths").select("id", count="exact").execute()
        high_confidence = db.table("payer_ivr_paths").select("id", count="exact").gte("confidence", 0.7).execute()

        return {
            "total_calls": total_calls.count or 0,
            "emergency_calls": emergency_calls.count or 0,
            "ivr_paths_learned": ivr_paths.count or 0,
            "high_confidence_paths": high_confidence.count or 0,
            "cost_per_minute": {
                "active_conversation": "$0.022-0.026",
                "on_hold": "~$0.001",
                "golden_ivr_path": "~$0.010"
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Call Control APIs ───────────────────────────────────────────────────────

@router.post("/calls/{call_sid}/end")
async def end_call(call_sid: str, request: Request):
    """Mark a call as ended and save final transcript"""
    body = await request.json()
    transcript = body.get("transcript", "")
    structured = body.get("structured_output", {})

    await update_call(call_sid, {"status": "completed"})

    if transcript:
        await save_transcript(call_sid, transcript, structured)

    return {"status": "call ended", "call_sid": call_sid}


@router.post("/ivr/{call_sid}/outcome")
async def record_ivr_outcome(call_sid: str, request: Request):
    """
    Record IVR navigation outcome.
    This triggers the learning reinforcement loop.
    """
    body = await request.json()
    success = body.get("success", False)
    duration_s = body.get("duration_s", 0)

    await ivr_navigator.record_outcome(call_sid, success, duration_s)

    return {
        "status": "outcome recorded",
        "call_sid": call_sid,
        "success": success,
        "learning": "path updated"
    }


# ─── Patient APIs ────────────────────────────────────────────────────────────

@router.get("/patients")
async def get_patients():
    """Get all patients"""
    from backend.core.database import get_db
    db = get_db()
    result = db.table("patients").select("*").order("created_at", desc=True).execute()
    return {"patients": result.data, "total": len(result.data)}


@router.post("/patients")
async def create_patient(request: Request):
    """Create a new patient record"""
    from backend.core.database import get_db
    body = await request.json()
    db = get_db()

    result = db.table("patients").insert({
        "name": body.get("name"),
        "dob": body.get("dob"),
        "phone": body.get("phone"),
        "insurance_name": body.get("insurance_name"),
        "clinic_id": body.get("clinic_id")
    }).execute()

    return {"patient": result.data[0], "status": "created"}


# ─── Clinic APIs ─────────────────────────────────────────────────────────────

@router.get("/clinics")
async def get_clinics():
    """Get all clinics"""
    from backend.core.database import get_db
    db = get_db()
    result = db.table("clinics").select("*").execute()
    return {"clinics": result.data}