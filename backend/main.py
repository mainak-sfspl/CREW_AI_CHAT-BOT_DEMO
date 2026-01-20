from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from backend.db_tool import SearchITDocsTool
from typing import List, Optional
import os

app = FastAPI(title="Sampurna IT Support Chatbot")

# Allow Frontend Connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# UPDATED: Request model now accepts chat_history
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List[str]] = []

def get_crew_response(user_question: str, history: List[str]):

    # 1. Format History for the Agent (Last 5 interactions)
    # We join the list into a single string context block
    context_str = "\n".join(history[-5:]) if history else "No previous context."

    # 2. Setup Gemini LLM (Lite version for speed/cost)
    my_llm = LLM(
        model="gemini/gemini-2.0-flash-lite-preview-02-05", 
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    search_tool = SearchITDocsTool()

    #3.Define the Agent (STRICT LANGUAGE SWITCHING)
    support_agent = Agent(
        role='Adaptive IT Support Specialist',
        goal='Provide accurate answers matching the user\'s current language strictly.',
        backstory=f"""You are Sampurna's Senior IT Support Bot.

        CRITICAL LANGUAGE RULE:
        - You must IGNORE the language of previous messages in the context.
        - Look ONLY at the 'CURRENT USER QUESTION'.
        - If the current question is in English, you MUST reply in English.
        - If the current question is in Bengali, you MUST reply in Bengali.
        - Never continue in the previous language if the user switches.

        OTHER RULES:
        1. MEMORY: Use the history only for facts (like names), not for language style.
        2. FORMATTING: Use bullet points for processes, short sentences for simple facts.
        """,
        verbose=True,
        allow_delegation=False,
        llm=my_llm,
        tools=[search_tool]
    )

    #4. Define the Task
    answer_task = Task(
        description=f"""
        CONTEXT HISTORY (For facts only):
        {context_str}

        CURRENT USER QUESTION:
        "{user_question}"

        INSTRUCTIONS:
        1. DETECT language of "{user_question}".
        2. IF English -> Output English. IF Bengali -> Output Bengali.
        3. Search database if needed.
        4. Answer the specific question.
        5. Output ONLY the answer.
        """,
        expected_output="A response in the exact same language as the Current User Question.",
        agent=support_agent
    )

    # 5. Run Crew
    tech_crew = Crew(
        agents=[support_agent],
        tasks=[answer_task],
        process=Process.sequential
    )

    result = tech_crew.kickoff()
    return result

@app.post("/ask")
async def ask_question(request: QueryRequest):
    try:
        # Pass both question and history to the agent
        result_object = get_crew_response(request.question, request.chat_history)
        final_answer = result_object.raw
        return {"answer": final_answer}
    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "Sampurna Chatbot API is running"}
