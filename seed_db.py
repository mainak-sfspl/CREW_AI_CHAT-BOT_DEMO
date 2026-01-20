import psycopg2
import pandas as pd
import ast

# Database connection parameters (matching your docker-compose)
DB_CONFIG = {
    "dbname": "vector_db",
    "user": "user",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

def seed_data():
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ Connected to database.")

        # Read the CSV file
        # ensure documents.csv is in the same folder
        df = pd.read_csv("documents.csv")
        print(f"📂 Found {len(df)} rows in CSV.")

        successful_inserts = 0

        for index, row in df.iterrows():
            try:
                # Prepare data
                doc_id = row['id']
                content = row['content']
                metadata = row['metadata']
                embedding = row['embedding']

                # SQL Insert Query
                insert_query = """
                INSERT INTO it_documents (id, content, metadata, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE 
                SET content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding;
                """
                
                cur.execute(insert_query, (doc_id, content, metadata, embedding))
                successful_inserts += 1

            except Exception as e:
                print(f"❌ Error inserting row {index}: {e}")

        # Commit changes
        conn.commit()
        cur.close()
        conn.close()
        print(f"🎉 Success! Inserted/Updated {successful_inserts} documents.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    seed_data()
