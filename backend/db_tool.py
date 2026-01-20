import os
import psycopg2
import json
from crewai.tools import BaseTool
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Load model once at module level so it doesn't reload every request
print("⏳ Loading embedding model...")
embedding_model = SentenceTransformer('all-mpnet-base-v2')
print("✅ Embedding model loaded.")

class SearchITDocsTool(BaseTool):
    name: str = "Search IT Documents"
    description: str = "Useful to search for IT support documents, policies, and FAQs. Input should be a specific question or keyword."

    def _run(self, query: str) -> str:
        try:
            # 1. Generate embedding
            query_vector = embedding_model.encode(query).tolist()

            # 2. Connect to DB
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            cur = conn.cursor()

            # 3. Search
            cur.execute(
                "SELECT content, similarity FROM match_it_documents(%s, 4, '{}')",
                (json.dumps(query_vector),)
            )
            results = cur.fetchall()

            cur.close()
            conn.close()

            if not results:
                return "No relevant documents found."

            # 4. Format
            formatted_results = "\n\n---\n\n".join(
                [f"Content: {row[0]}\n(Confidence: {row[1]:.2f})" for row in results]
            )
            return formatted_results

        except Exception as e:
            return f"Error searching database: {str(e)}"
