from __future__ import annotations

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from auth_router import get_current_user, require_role
from database import (
    get_all_results,
    get_all_patients,
    get_conn,
    get_linked_patient_ids,
    get_signals,
    get_user_by_id,
    link_caregiver_to_patient,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me")
def my_analytics(user: dict = Depends(get_current_user)):
    """Return analytics for the authenticated patient."""
    user_id = int(user["id"])

    with get_conn() as conn:
        result_rows = conn.execute(
            "SELECT created_at, mmse_total, ml_prediction, agreement FROM screening_results WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()

    trend = [dict(r) for r in result_rows]
    signals = get_signals(user_id=user_id, days=90)

    return {
        "mmse_trend": trend,
        "signals": [
            {
                **s,
                "alert_keywords": json.loads(s.get("alert_keywords") or "[]"),
            }
            for s in signals
        ],
    }


@router.get("/caregiver/patients")
def caregiver_overview(caregiver: dict = Depends(require_role("caregiver"))):
    """Return aggregate screening results for patients linked to this caregiver."""
    linked_ids = set(get_linked_patient_ids(int(caregiver["id"])))
    results = get_all_results()
    filtered = [r for r in results if int(r.get("user_id") or 0) in linked_ids]
    return {"results": filtered}


@router.get("/caregiver/patient")
def get_linked_patient(caregiver: dict = Depends(require_role("caregiver"))):
    """Return the patient linked to this caregiver.
    
    If no explicit link exists, auto-links the caregiver to the most recently
    registered patient so the Memory Vault works immediately after sign-in.
    """
    caregiver_id = int(caregiver["id"])
    linked_ids = get_linked_patient_ids(caregiver_id)

    if not linked_ids:
        # Auto-link: pick the most recently registered patient
        all_pts = get_all_patients()
        if not all_pts:
            raise HTTPException(status_code=404, detail="No patients registered in the system")
        # Use the last registered patient (highest id) as the default
        default_patient = sorted(all_pts, key=lambda p: p["id"], reverse=True)[0]
        link_caregiver_to_patient(caregiver_id, default_patient["id"])
        return {"id": default_patient["id"], "full_name": default_patient["full_name"], "email": default_patient.get("email", "")}

    patient = get_user_by_id(linked_ids[0])
    if not patient:
        raise HTTPException(status_code=404, detail="Linked patient not found")
    return {"id": patient["id"], "full_name": patient["full_name"], "email": patient.get("email", "")}


@router.get("/caregiver/patients-list")
def list_all_patients(caregiver: dict = Depends(require_role("caregiver"))):
    """Return all registered patients so a caregiver can select one to link."""
    patients = get_all_patients()
    linked_ids = set(get_linked_patient_ids(int(caregiver["id"])))
    return [
        {**p, "linked": p["id"] in linked_ids}
        for p in patients
    ]


@router.post("/caregiver/link")
def link_patient(
    patient_id: int = Body(..., embed=True),
    caregiver: dict = Depends(require_role("caregiver")),
):
    """Explicitly link a patient to the authenticated caregiver."""
    patient = get_user_by_id(patient_id)
    if not patient or patient.get("role") != "patient":
        raise HTTPException(status_code=400, detail="Invalid patient_id — user not found or not a patient")
    created = link_caregiver_to_patient(int(caregiver["id"]), patient_id)
    return {
        "linked": True,
        "created": created,
        "patient": {"id": patient["id"], "full_name": patient["full_name"]},
    }
