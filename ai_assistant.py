"""
Gemini 2.5 Flash AI layer — using the official google-genai SDK.
All prompts are kept in one place to make them easy to update.
"""

from google import genai
from google.genai import types
from matching_engine import BLOOD_COMPATIBILITY, ORGANS

_MODEL_NAME = "gemini-2.5-flash"
_api_key: str | None = None


def init_gemini(api_key: str):
    global _api_key
    _api_key = api_key.strip()


def _client():
    if not _api_key:
        raise RuntimeError("Gemini API key not configured.")
    return genai.Client(api_key=_api_key)


# ── 1. AI Match Explanation ───────────────────────────────────────────────────

def explain_match(donor: dict, request: dict, score: float) -> str:
    """
    Generate a short, compassionate explanation of why this donor is a good
    match for this patient's request.
    """
    if not _api_key:
        return "AI explanation unavailable (API key not configured)."

    prompt = f"""
You are a medical coordination assistant for a life-saving organ & blood donation platform.

Explain — in 3–4 concise, empathetic sentences — why the following donor is a strong match
for the patient's request. Mention blood-type compatibility, organ availability, and proximity.
Keep the tone warm and professional. Do NOT add any disclaimer or legal text.

DONOR
  Name        : {donor.get('name')}
  Blood Type  : {donor.get('blood_type')}
  Available Organs : {', '.join(donor.get('organs', []))}
  Location    : {donor.get('city')}, {donor.get('state')}

PATIENT REQUEST
  Patient     : {request.get('patient_name')}
  Blood Type  : {request.get('blood_type')}
  Needs       : {request.get('needed_organ')}
  Hospital    : {request.get('hospital')}, {request.get('city')}, {request.get('state')}
  Urgency     : {request.get('urgency')}

MATCH SCORE : {score:.2%}

Write the explanation now:
"""
    try:
        client = _client()
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"AI explanation unavailable: {e}"


# ── 2. AI Triage Assistant (chatbot) ─────────────────────────────────────────

def triage_chat(conversation_history: list[dict], user_message: str) -> str:
    """
    Stateful triage chat.
    conversation_history = list of {"role": "user"|"model", "content": "text"} dicts.
    """
    if not _api_key:
        return "AI Assistant unavailable (API key not configured)."

    system_prompt = f"""
You are LifeLink AI, a compassionate and knowledgeable medical assistant
on a blood and organ donation coordination platform.

Your capabilities:
- Answer questions about blood type compatibility.
- Explain which blood types / organs are compatible.
- Guide donors through the registration process.
- Explain what happens after a match is found.
- Provide general medical information about organ donation.
- Offer emotional support to families waiting for a match.

Blood compatibility chart (donor → recipient):
{BLOOD_COMPATIBILITY}

Available organs on the platform:
{', '.join(ORGANS)}

Rules:
- Always be concise, warm, and professional.
- Never give specific medical advice or diagnosis.
- If unsure, recommend contacting the hospital directly.
- Respond in plain text (no Markdown).
"""
    try:
        client = _client()

        # Build contents list from history + new message
        contents = []
        for msg in conversation_history:
            role = msg["role"]  # "user" or "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])],
                )
            )
        # Add the new user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)],
            )
        )

        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return f"AI unavailable: {e}"


# ── 3. Donor Health Tips ──────────────────────────────────────────────────────

def donor_health_tips(blood_type: str, organs: list[str]) -> str:
    """Return personalised health preparation tips for a donor."""
    if not _api_key:
        return "AI tips unavailable (API key not configured)."

    prompt = f"""
You are a health advisor for organ and blood donors.

Give 5 concise, practical health tips to help this donor prepare for donation.
Tailor the tips to the blood type and the organs they intend to donate.
Format as a numbered list. Be encouraging.

Blood type : {blood_type}
Organs     : {', '.join(organs) if organs else 'Blood only'}
"""
    try:
        client = _client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI tips unavailable: {e}"


# ── 4. Request Urgency Analysis ───────────────────────────────────────────────

def analyze_urgency(patient_notes: str, organ: str, age: int) -> str:
    """Analyze the notes and suggest urgency level with reasoning."""
    if not _api_key:
        return "AI analysis unavailable (API key not configured)."

    prompt = f"""
You are a medical triage expert for an organ donation coordination system.

Based on the following patient information, suggest a urgency level
(Critical / High / Medium / Low) and give a one-sentence justification.
Respond with exactly this format:
  Urgency: <level>
  Reason : <one sentence>

Patient age    : {age}
Organ needed   : {organ}
Clinical notes : {patient_notes or 'None provided'}
"""
    try:
        client = _client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI analysis unavailable: {e}"


# ── 5. Platform Statistics Summary ───────────────────────────────────────────

def generate_stats_summary(stats: dict) -> str:
    """Generate a human-readable summary of platform statistics."""
    if not _api_key:
        return "AI summary unavailable (API key not configured)."

    prompt = f"""
You are an analyst for a life-saving organ and blood donation platform.

Write a 3–4 sentence uplifting paragraph summarising these platform statistics
for a public-facing dashboard. Highlight impact, urgency, and call to action.

Statistics:
- Total donors registered   : {stats.get('total_donors', 0)}
- Active (available) donors : {stats.get('active_donors', 0)}
- Open urgent requests       : {stats.get('open_requests', 0)}
- Matches made so far        : {stats.get('total_matches', 0)}
- Most requested organ       : {stats.get('top_organ', 'N/A')}
- Most common blood type     : {stats.get('top_blood', 'N/A')}
"""
    try:
        client = _client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI summary unavailable: {e}"
