"""FastAPI backend server and SQLite API for VALENCE."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from db import create_case, delete_case, get_case, init_db, list_cases, list_statutes, update_case_status
from engine import analyze_voice_input

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="VALENCE API", version="1.0.0", lifespan=lifespan)
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=3000)
    language: str = Field(default="en-IN")
    clarification: str | None = Field(default=None, max_length=500)
    auto_save: bool = Field(default=True)


class UpdateStatusRequest(BaseModel):
    status: Literal["Drafted", "RTI Filed", "Resolved"]


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "database": "sqlite",
        "gemini_configured": "yes" if os.getenv("GEMINI_API_KEY") else "optional",
    }


@app.get("/api/statutes")
def get_statutes() -> dict[str, list]:
    return {"statutes": list_statutes()}


@app.post("/api/analyze")
def analyze_endpoint(
    body: AnalyzeRequest,
    x_gemini_key: str | None = Header(default=None),
):
    result = analyze_voice_input(
        transcript=body.transcript,
        language=body.language,
        clarification=body.clarification,
        api_key=x_gemini_key,
    )
    if result.get("needs_clarification"):
        return result

    if body.auto_save:
        saved = create_case(result)
        result["id"] = saved["id"]
        result["status"] = saved["status"]
        result["created_at"] = saved["created_at"]
    return result


@app.get("/api/cases")
def get_all_cases():
    return {"cases": list_cases()}


@app.get("/api/cases/{case_id}")
def get_single_case(case_id: int):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.patch("/api/cases/{case_id}")
def patch_case_status(case_id: int, body: UpdateStatusRequest):
    updated = update_case_status(case_id, body.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Case not found")
    return updated


@app.delete("/api/cases/{case_id}")
def remove_case(case_id: int):
    if not delete_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return {"deleted": True, "id": case_id}


@app.get("/api/cases/{case_id}/export")
def export_case_dossier(case_id: int):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    content = (
        f"================================================================\n"
        f"VALENCE — STATUTORY ACTION DOSSIER [{case['case_code']}]\n"
        f"================================================================\n"
        f"Department: {case['department']}\n"
        f"Violation:  {case['violation_title']}\n"
        f"Statute:    {case['statute_ref']}\n"
        f"Status:     {case['status']}\n"
        f"Created:    {case['created_at']}\n\n"
        f"--- IN-EAR ASSERTIVENESS SCRIPT ---\n"
        f"{case['in_ear_script']}\n\n"
        f"--- FORM A: RTI APPLICATION (SECTION 6 & 20) ---\n"
        f"{case['rti_draft']}\n\n"
        f"--- CPGRAMS GRIEVANCE DRAFT ---\n"
        f"{case['grievance_draft']}\n"
    )
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{case["case_code"]}_dossier.txt"'},
    )


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
