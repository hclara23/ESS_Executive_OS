import os
import datetime
import psycopg2
from pypdf import PdfReader
from Features.PostgresStore import _connect
from dotenv import load_dotenv
from server.ai_provider import create_embeddings

load_dotenv()

def generate_embeddings(text):
    """
    Generates embeddings using the active local/cloud provider.
    """
    try:
        response = create_embeddings(text)
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def chunk_text(text, size=1000):
    """Simple text chunker."""
    return [text[i:i+size] for i in range(0, len(text), size)]

def ingest_pdf(file_path, file_name):
    """Parses a PDF, chunks it, and saves embeddings to the knowledge base."""
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        if not full_text.strip():
            return False, "No text could be extracted from the PDF."

        chunks = chunk_text(full_text)
        
        conn = _connect()
        if not conn:
            return False, "Database connection failed."
        
        cur = conn.cursor()
        
        for i, chunk in enumerate(chunks):
            embedding = generate_embeddings(chunk)
            if embedding:
                cur.execute(
                    """
                    insert into elio_knowledge_base (file_name, content, embedding, created_at)
                    values (%s, %s, %s, %s);
                    """,
                    (file_name, chunk, embedding, datetime.datetime.utcnow())
                )
        
        conn.commit()
        cur.close()
        conn.close()
        return True, f"PDF ingested into {len(chunks)} searchable segments."
    except Exception as e:
        return False, str(e)

def search_knowledge_base(query, limit=3):
    """Performs a semantic vector search across the knowledge base."""
    try:
        query_embedding = generate_embeddings(query)
        if not query_embedding:
            return []

        conn = _connect()
        if not conn:
            return []
        
        cur = conn.cursor()
        # Semantic search using cosine distance (<=>)
        cur.execute(
            """
            select file_name, content, 1 - (embedding <=> %s) as similarity
            from elio_knowledge_base
            order by similarity desc
            limit %s;
            """,
            (query_embedding, limit)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                "file": r[0], 
                "snippet": r[1][:500] + "...",
                "score": r[2]
            })
        return results
    except Exception as e:
        print(f"Knowledge Search Error: {e}")
        return []

def list_knowledge_files():
    """Lists all files stored in the knowledge base table."""
    try:
        conn = _connect()
        if not conn:
            return []
        
        cur = conn.cursor()
        cur.execute("select distinct file_name from elio_knowledge_base order by file_name asc;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print(f"Knowledge List Error: {e}")
        return []

def delete_knowledge_file(file_name):
    """Removes a file and its segments from the knowledge base."""
    try:
        conn = _connect()
        if not conn: return False
        cur = conn.cursor()
        cur.execute("delete from elio_knowledge_base where file_name = %s;", (file_name,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Delete Knowledge Error: {e}")
        return False
