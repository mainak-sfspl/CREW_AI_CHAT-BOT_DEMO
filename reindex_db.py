import os
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Database Config
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "vector_db"),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def reindex_data():
    try:
        # 1. Load the Model
        print("⏳ Loading model (this may take a moment)...")
        model = SentenceTransformer('all-mpnet-base-v2')
        print("✅ Model loaded.")

        # 2. Connect to DB
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 3. Fetch all documents (id and content only)
        print("⏳ Fetching documents...")
        cur.execute("SELECT id, content FROM it_documents WHERE content IS NOT NULL")
        rows = cur.fetchall()
        total = len(rows)
        print(f"📂 Found {total} documents to re-index.")

        # 4. Loop and Update
        count = 0
        for row in rows:
            doc_id = row[0]
            content = row[1]

            # Generate new valid embedding
            new_embedding = model.encode(content).tolist()

            # Update the row
            cur.execute(
                "UPDATE it_documents SET embedding = %s WHERE id = %s",
                (str(new_embedding), doc_id)
            )

            count += 1
            if count % 100 == 0:
                print(f"   Processed {count}/{total}...")
                conn.commit() # Commit in batches

        conn.commit()
        cur.close()
        conn.close()
        print(f"🎉 Success! Re-indexed all {total} documents.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reindex_data()
