"""Voice-to-rights statutory analysis and regional coaching engine for VALENCE."""

from __future__ import annotations

import json
import os
import random
import re
from datetime import datetime
from typing import Any

from db import list_statutes

CLARIFICATION_PROMPTS: dict[str, str] = {
    "en-IN": "Which office or service is this—electricity, water supply, traffic police, or municipal desk?",
    "hi-IN": "यह किस विभाग से जुड़ा मामला है—बिजली, पानी, ट्रैफिक पुलिस, या नगर निगम?",
    "hinglish": "Ye kis department ka matter hai—bijli, paani, traffic police, ya municipal office?",
    "ta-IN": "இது எந்தத் துறை சம்பந்தப்பட்டது—மின்சாரம், குடிநீர், போக்குவரத்து காவல், அல்லது நகராட்சி?",
    "mr-IN": "हे कोणत्या विभागाशी संबंधित आहे—वीज, पाणी, वाहतूक पोलीस, की महापालिका?",
    "te-IN": "ఇది ఏ విభాగానికి సంబంధించినది—విద్యుత్, నీరు, ట్రాఫిక్ పోలీస్, లేదా మున్సిపల్ ఆఫీస్?",
    "bn-IN": "এটি কোন দপ্তরের বিষয়—বিদ্যুৎ, জল সরবরাহ, ট্রাফিক পুলিশ, নাকি পৌরসভা?",
}

REGIONAL_SYNONYMS: dict[str, list[str]] = {
    "electricity-disconnection": [
        "bijli", "electricity", "power", "meter", "lineman", "current", "wire",
        "बिजली", "मीटर", "लाइनमैन", "तार", "மின்சாரம்", "वीज", "విద్యుత్", "বিদ্যুৎ",
    ],
    "municipal-water-cut": [
        "water", "paani", "pani", "pipeline", "tap", "nal", "valve", "tanker",
        "पानी", "नल", "पाइप", "குடிநீர்", "தண்ணீர்", "पाणी", "నీరు", "জল",
    ],
    "traffic-rto-extortion": [
        "traffic", "police", "rto", "license", "licence", "challan", "key", "keys",
        "chabi", "bike", "car", "vehicle", "gaadi", "helmet", "signal",
        "ट्रैफिक", "चाबी", "चालान", "लाइसेंस", "गाड़ी", "போக்குவரத்து", "सावी", "वाहतूक", "ట్రాఫిక్", "ট্রাফিক",
    ],
    "certificate-office-bribe": [
        "certificate", "bribe", "cash", "babu", "clerk", "tehsil", "passport",
        "income", "caste", "domicile", "birth", "delay", "pending", "rishwat",
        "ghoos", "रिश्वत", "बाबू", "प्रमाणपत्र", "பணம்", "लाच", "లంచం", "ঘুষ",
    ],
    "police-fir-refusal": [
        "fir", "thana", "station", "theft", "stolen", "assault", "scam", "fraud",
        "cyber", "refused", "थाना", "एफआईआर", "चोरी", "காவல்", "एफआयआर", "ఎఫ్ఐఆర్", "থানা",
    ],
    "civic-sanitation-road": [
        "pothole", "road", "garbage", "trash", "kachra", "drain", "gutter",
        "streetlight", "sadak", "सड़क", "कचरा", "गड्ढा", "சாலை", "रस्ता", "రోడ్డు", "রাস্তা",
    ],
}


def _extract_amount(text: str) -> str | None:
    patterns = [
        r"(?:₹|rs\.?|inr|rupees?|रुपये|रुपए)\s*([0-9][0-9,]{1,6})",
        r"([0-9][0-9,]{1,6})\s*(?:₹|rs\.?|inr|rupees?|cash|fine|bribe|रुपये|रुपए|नकद|कैश)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            digits = match.group(1).replace(",", "")
            return f"₹{int(digits):,}"
    return None


def _extract_location(text: str) -> str | None:
    match = re.search(
        r"\b(?:at|near|in|ward|sector|block|road|nagar|colony|chowk)\s+([A-Za-z0-9\-\s]{2,26})",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        cleaned = re.split(r"[,.]| and | but | demanding | asking ", match.group(1), maxsplit=1)[0].strip()
        if cleaned:
            return cleaned[:36]
    return None


HIGH_SIGNAL_TERMS: dict[str, set[str]] = {
    "electricity-disconnection": {"electricity", "power", "meter", "bijli", "vidyut", "bijuli", "minsaaram", "बिजली", "मीटर", "மின்சாரம்", "वीज", "విద్యుత్", "বিদ্যুৎ"},
    "municipal-water-cut": {"water", "paani", "pani", "pipeline", "tap", "nal", "पानी", "नल", "पाइप", "குடிநீர்", "தண்ணீர்", "पाणी", "నీరు", "জল"},
    "traffic-rto-extortion": {"traffic", "rto", "challan", "license", "licence", "keys", "chabi", "ट्रैफिक", "चाबी", "चालान", "போக்குவரத்து", "वाहतूक", "ట్రాఫిక్", "ট্রাফিক"},
    "certificate-office-bribe": {"certificate", "tehsil", "passport", "income", "caste", "domicile", "तहसील", "प्रमाणपत्र"},
    "police-fir-refusal": {"fir", "thana", "stolen", "assault", "cyber", "थाना", "एफआईआर", "காவல்", "एफआयआर", "ఎఫ్ఐఆర్", "থানা"},
    "civic-sanitation-road": {"pothole", "road", "garbage", "kachra", "drain", "gutter", "streetlight", "सड़क", "कचरा", "சாலை", "रस्ता", "రోడ్డు", "রাস্তা"},
}


def _match_statute(text: str, statutes: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, int]:
    lowered = text.lower()
    best_statute = None
    best_score = 0

    for st in statutes:
        score = 0
        slug = st["slug"]
        high_terms = HIGH_SIGNAL_TERMS.get(slug, set())
        seen: set[str] = set()
        for term in list(st["keywords"]) + REGIONAL_SYNONYMS.get(slug, []):
            t = term.lower()
            if t in seen:
                continue
            seen.add(t)
            if t in lowered:
                score += 4 if t in high_terms else 1
        if score > best_score:
            best_score = score
            best_statute = st

    return best_statute, best_score


def _generate_case_code() -> str:
    return f"VLC-{random.randint(1000, 9999)}"


def _build_rti_draft(
    case_code: str,
    statute: dict[str, Any],
    transcript: str,
    amount: str | None,
    location: str | None,
) -> str:
    today_str = datetime.now().strftime("%d %B %Y")
    loc_line = f"\nIncident Location / Ward: {location}" if location else ""
    amt_line = f"\nAlleged Unreceipted Cash Demand: {amount}" if amount else ""

    questions = list(statute["rti_questions"])
    if amount:
        questions.append(
            f"Provide the official justification and legal receipt series for demanding {amount} in cash."
        )

    q_block = "\n".join(f"{idx}. {q}" for idx, q in enumerate(questions, start=1))

    return (
        f"FORM A — APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005\n"
        f"Date: {today_str} | Reference: {case_code}\n\n"
        f"To,\nThe Public Information Officer (PIO),\n{statute['pio_designation']}\n\n"
        f"Subject: Mandatory Record Disclosure — {statute['violation_title']} ({statute['statute_ref']})\n"
        f"Statutory Disposal Limit: 30 Days (Section 7(1)) | Personal Officer Fine: ₹250/day up to ₹25,000 (Section 20)\n\n"
        f"Respected Sir/Madam,\n"
        f"Under Section 6(1) of the Right to Information Act, 2005, please supply certified copies of the following official records:\n\n"
        f"{q_block}\n\n"
        f"Factual Summary Recorded:{loc_line}{amt_line}\n"
        f"\"{transcript.strip()}\"\n\n"
        f"Notice: Failure to furnish accurate records within 30 days (or 48 hours where life/liberty applies) attracts "
        f"personal financial penalty under Section 20(1) and disciplinary proceedings under Section 20(2) of the RTI Act, 2005."
    )


def _build_grievance_draft(
    case_code: str,
    statute: dict[str, Any],
    transcript: str,
    amount: str | None,
    location: str | None,
) -> str:
    today_str = datetime.now().strftime("%d %B %Y")
    amount_note = f" and unreceipted cash demand of {amount}" if amount else ""
    location_note = f" at {location}" if location else ""

    return (
        f"CPGRAMS / STATE CITIZEN CHARTER GRIEVANCE [{case_code}]\n"
        f"Date: {today_str}\n"
        f"Department: {statute['department']}\n"
        f"Statutory Clause Invoked: {statute['statute_ref']}\n"
        f"Mandatory Citizen Charter SLA: {statute['sla_days']} Day(s)\n\n"
        f"Grievance Statement:\n"
        f"The citizen reports {statute['violation_title'].lower()}{location_note}{amount_note}.\n\n"
        f"Spoken Testimony:\n\"{transcript.strip()}\"\n\n"
        f"Action Requested:\n"
        f"1. Immediate restoration / service disposal within the {statute['sla_days']}-day Citizen Charter SLA.\n"
        f"2. Departmental inquiry into official non-compliance and prevention of informal cash demands.\n"
        f"3. Parallel RTI Form-A ({case_code}) logged for inspection log and work order verification."
    )


def _try_gemini_enrichment(
    api_key: str,
    transcript: str,
    language: str,
    statute: dict[str, Any],
    case_code: str,
    amount: str | None,
) -> dict[str, str] | None:
    """Optionally refine the localized in-ear script & drafts with Gemini if user supplies a key."""
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are VALENCE, a civic legal shield for India. Return strictly valid JSON with keys "
            f"`in_ear_script`, `rti_draft`, `grievance_draft`.\n"
            f"User transcript: {transcript}\n"
            f"Target language code for in_ear_script ONLY: {language} (keep it natural, calm, under 40 words, "
            f"naming case code {case_code} and statute {statute['statute_ref']}).\n"
            f"Matched Statute: {statute['violation_title']} ({statute['statute_ref']}), PIO: {statute['pio_designation']}, "
            f"Amount mentioned: {amount or 'None'}.\n"
            f"Keep rti_draft as a concise Form-A RTI under Section 6(1) & Section 20 (₹250/day penalty). "
            f"Keep grievance_draft concise for CPGRAMS."
        )
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = (resp.text or "").strip()
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
        parsed = json.loads(raw)
        if all(k in parsed for k in ("in_ear_script", "rti_draft", "grievance_draft")):
            return {
                "in_ear_script": str(parsed["in_ear_script"]),
                "rti_draft": str(parsed["rti_draft"]),
                "grievance_draft": str(parsed["grievance_draft"]),
            }
    except Exception:
        return None
    return None


def analyze_voice_input(
    transcript: str,
    language: str = "en-IN",
    clarification: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Analyze spoken citizen input, request clarification if vague, or compile full statutory dossier."""
    combined = f"{transcript.strip()} {clarification.strip() if clarification else ''}".strip()
    statutes = list_statutes()
    matched, score = _match_statute(combined, statutes)

    if len(combined.split()) < 3 or matched is None or score == 0:
        return {
            "needs_clarification": True,
            "clarification_question": CLARIFICATION_PROMPTS.get(language, CLARIFICATION_PROMPTS["en-IN"]),
            "language": language,
            "combined_transcript": combined,
        }

    case_code = _generate_case_code()
    amount = _extract_amount(combined)
    location = _extract_location(combined)

    templates = matched["in_ear_templates"]
    in_ear_script = templates.get(language, templates["en-IN"]).format(case_code=case_code)
    rti_draft = _build_rti_draft(case_code, matched, combined, amount, location)
    grievance_draft = _build_grievance_draft(case_code, matched, combined, amount, location)
    engine_mode = "statutory-rag"

    effective_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if effective_key:
        enriched = _try_gemini_enrichment(effective_key, combined, language, matched, case_code, amount)
        if enriched:
            in_ear_script = enriched["in_ear_script"]
            rti_draft = enriched["rti_draft"]
            grievance_draft = enriched["grievance_draft"]
            engine_mode = "gemini-statutory-rag"

    return {
        "needs_clarification": False,
        "case_code": case_code,
        "language": language,
        "transcript": combined,
        "department": matched["department"],
        "violation_title": matched["violation_title"],
        "statute_ref": matched["statute_ref"],
        "sla_days": matched["sla_days"],
        "penalty_note": matched["penalty_note"],
        "extortion_amount": amount,
        "location_hint": location,
        "in_ear_script": in_ear_script,
        "rti_draft": rti_draft,
        "grievance_draft": grievance_draft,
        "engine_mode": engine_mode,
    }
