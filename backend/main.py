from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from backend.db_tool import SearchITDocsTool
from typing import List, Optional
import os
import base64

# --- Modern Google Client ---
from google import genai
from google.genai import types


app = FastAPI(title="Sampurna IT Support Chatbot (Enhanced)")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Data Models
# ---------------------------
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[str]] = []
    image_data: Optional[str] = None


# ---------------------------
# Global clients (speed)
# ---------------------------
GOOGLE_API_KEY = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
if not GOOGLE_API_KEY:
    print("⚠️ Missing GOOGLE_API_KEY / GEMINI_API_KEY in env")

genai_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None


# ---------------------------
# Helper: parse data-uri MIME
# ---------------------------
def _parse_data_uri(data_uri: str):
    """
    Returns (mime_type, base64_payload)
    """
    if not data_uri:
        return ("image/png", "")
    if "," in data_uri and data_uri.startswith("data:"):
        header, b64 = data_uri.split(",", 1)
        # header like: data:image/png;base64
        mime = header.split(";")[0].replace("data:", "").strip() or "image/png"
        return (mime, b64)
    # raw base64 fallback
    return ("image/png", data_uri)


# ---------------------------
# Vision Analysis (OCR + Visual)
# ---------------------------
def analyze_image(base64_string: str) -> str:
    try:
        if not genai_client:
            return "Vision unavailable: missing API key."

        mime_type, b64_payload = _parse_data_uri(base64_string)
        image_bytes = base64.b64decode(b64_payload)

        text_prompt = """
You are an advanced AI Vision System. Perform two distinct tasks:
1) OCR EXTRACTION: Read visible text verbatim.
2) VISUAL ANALYSIS: Describe the technical scene (e.g., 'error dialog', '404 page', 'login failed').

Return format exactly:
[OCR RAW TEXT]: ...
[VISUAL CONTEXT]: ...
""".strip()

        response = genai_client.models.generate_content(
            model="gemini-2.0-flash-lite-preview-02-05",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_text(text=text_prompt),
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ]
                )
            ],
        )
        return (response.text or "").strip() or "No image insights found."
    except Exception as e:
        print(f"Vision Error: {repr(e)}")
        return "Error analyzing image."


# ---------------------------
# Query normalization (THIS FIXES tab/tablet lost)
# ---------------------------
def normalize_query(q: str) -> str:
    """
    Fixes common ambiguity + boosts retrieval for near-match.
    - 'tab' => tablet device (unless chrome/browser mentioned)
    - lost/stolen => asset loss keywords appended
    """
    t = (q or "").strip()
    low = t.lower()

    # If user says tab but not chrome/browser -> treat as tablet device
    if "tab" in low and ("chrome" not in low and "browser" not in low):
        # Replace standalone 'tab' meaningfully
        # Keep original too (helps retrieval)
        t = f"{t} (tablet device / office tablet)"

    # Lost/stolen cases -> push asset-loss cluster
    if any(k in low for k in ["lost", "missing", "stolen", "churi", "chুরি", "হার", "lost tab", "lost tablet", "laptop lost"]):
        t = t + " asset loss policy device lost stolen penalty annexure tms ticket helpdesk"

    # Too generic -> expand to policy list terms so it still retrieves something
    if low in {"it policy", "policy", "it policies", "it"}:
        t = "acceptable use policy password policy data security policy vpn policy asset loss policy laptop policy"

    return t.strip()


# ---------------------------
# Core Logic
# ---------------------------
def get_crew_response(user_question: str, history: List[str], image_data: str = None):
    # Context Memory: last 5 chat messages
    recent_history = history[-5:] if history else []
    context_str = "\n".join(recent_history) if recent_history else "No previous context."

    # Image
    image_description = None
    image_context = ""
    if image_data:
        print("📸 Image detected! Running Analysis...")
        image_description = analyze_image(image_data)
        image_context = f"\n[IMAGE ANALYSIS REPORT]:\n{image_description}\n"

    # Normalize query for better retrieval + ambiguity fix
    normalized_question = normalize_query(user_question)

    # LLM (CrewAI wrapper)
    my_llm = LLM(
        model="gemini/gemini-2.0-flash-lite-preview-02-05",
        api_key=GOOGLE_API_KEY
    )

    # ✅ Updated Agent: NO "can't access docs" lines, always answer using near match
    support_agent = Agent(
        role="Sampurna Senior IT Specialist",
        goal="Provide fast, polite, detailed, policy-grounded IT support using internal documents.",
        backstory = """
You are Sampurna IT Support — friendly, precise, typo-tolerant, multilingual, and context-aware.

CRITICAL BEHAVIOR RULES:
1) You MUST use SearchITDocsTool for every query. Use the retrieved policy text as your source.
2) NEVER say "I cannot access the IT documentation/database" or "technical difficulties" if the backend is running.
   If retrieval returns nothing, DO THIS INSTEAD:
   - Use near-match policy topics (asset loss, stolen device, laptop policy, penalties, ticket/TMS process)
   - Provide the best policy-guided steps anyway.
   - Phrase it as: "Based on the closest matching policy sections, here is what to do."
3) DISAMBIGUATION (VERY IMPORTANT):
   - "tab" / "ট্যাব" / "टैब" means "tablet device" (office TAB) unless the user explicitly says "browser tab" or "Chrome tab".
   - "laptop lost" / "tablet lost" / "device lost" are asset-loss cases.
4) LANGUAGE:
   - Detect language (English/Hindi/Bengali).
   - Internally search in English terms (translate if needed).
   - Reply in the same language as the user.
5) OUTPUT:
   - Always give the answer (no blank replies).
   - Prefer bullet points for steps and details.
   - Include related/near matches when helpful.
6) If policy lacks a numeric detail (amount/date), say: "The policy document does not mention this detail."
""".strip(),
        verbose=True,
        allow_delegation=False,
        llm=my_llm,
        tools=[SearchITDocsTool()]
    )

    # Task prompt: focuses on retrieval + answering (no whining)
    final_prompt = f"""
CONTEXT (Last 5 Messages):
{context_str}

VISUAL CONTEXT:
{image_context}

USER QUESTION (original): "{user_question}"
USER QUESTION (normalized for search): "{normalized_question}"

YOUR MISSION:
1) Search internal IT docs using SearchITDocsTool with the normalized question.
2) If image is provided, combine OCR text + visual context with retrieved policy steps.
3) Provide the best possible policy-aligned answer even if it is a near match.
4) Output in bullets:
   - Summary
   - Steps to follow
   - Required details/info (serial number, employee ID, location, time)
   - Escalation/contact (only if present in docs)
   - Penalties/charges (only if present in docs)
   - Related policies (if any)
""".strip()

    answer_task = Task(
        description=final_prompt,
        expected_output="A policy-grounded, actionable IT support answer in bullet points.",
        agent=support_agent
    )

    tech_crew = Crew(
        agents=[support_agent],
        tasks=[answer_task],
        process=Process.sequential
    )

    result = tech_crew.kickoff()

    return {
        "answer": (result.raw or "").strip(),
        "image_description": image_description
    }


# ---------------------------
# API Endpoints
# ---------------------------
@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        result_dict = get_crew_response(
            request.question,
            request.chat_history or [],
            request.image_data
        )

        answer = (result_dict.get("answer") or "").strip()
        if not answer:
            # No empty responses
            answer = "Please share a bit more detail (example: 'tablet device lost', 'vpn setup', 'laptop policy')."

        return {"answer": answer}

    except Exception as e:
        # IMPORTANT: Don't return DB/technical apology templates.
        print(f"Ask Error: {repr(e)}")
        return {
            "answer": "I couldn’t complete the policy lookup for that query. Try a clearer keyword like: 'tablet lost', 'asset loss policy', 'stolen laptop', 'vpn setup', or paste the exact error text."
        }


@app.get("/")
def read_root():
    return {"status": "Sampurna Enhanced API is running"}


@app.get("/health")
def health():
    return {"ok": True}
