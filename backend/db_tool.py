import os
import psycopg2
from crewai.tools import BaseTool
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

print("⏳ Loading embedding model...")
embedding_model = SentenceTransformer("all-mpnet-base-v2")
print("✅ Embedding model loaded.")


def _to_pgvector(vec) -> str:
    # pgvector text input format: [0.1,0.2,...]
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


class SearchITDocsTool(BaseTool):
    name: str = "Search IT Documents"
    description: str = "Search IT support documents, policies, and FAQs. Input should be a specific question or keyword."

    def _run(self, query: str) -> str:
        query = (query or "").strip()
        if not query:
            return "No relevant documents found."

        try:
            query_vector = embedding_model.encode(query).tolist()
            vec_str = _to_pgvector(query_vector)

            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            cur = conn.cursor()

            cur.execute(
                """
                SELECT content, similarity
                FROM match_it_documents(%s::vector, %s, %s::jsonb)
                """,
                (vec_str, 4, "{}"),
            )
            results = cur.fetchall()
            cur.close()
            conn.close()

            if not results:
                return "No relevant documents found."

            return "\n\n---\n\n".join(
                [f"Content: {row[0]}\n(Confidence: {float(row[1]):.2f})" for row in results]
            )

        except Exception as e:
            # ✅ do NOT poison the LLM with DB errors
            print("DB search error:", repr(e))
            return "No relevant documents found."
