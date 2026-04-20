import os
import sys
from pathlib import Path

# Add project root to sys.path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from Features.KnowledgeBase import ingest_pdf, list_knowledge_files

def preload_knowledge(directory="Data/Knowledge"):
    """
    Scans a directory for PDF files and ingests them into the knowledge base if not already present.
    """
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist. Creating it...")
        os.makedirs(directory)
        return

    existing_files = list_knowledge_files()
    files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    
    if not files:
        print(f"No PDF files found in {directory}.")
        return

    print(f"Found {len(files)} PDFs in {directory}. Starting ingestion...")
    
    for filename in files:
        if filename in existing_files:
            print(f"Skipping {filename} (already in knowledge base).")
            continue
            
        file_path = os.path.join(directory, filename)
        print(f"Ingesting {filename}...")
        success, message = ingest_pdf(file_path, filename)
        if success:
            print(f"Successfully ingested {filename}: {message}")
        else:
            print(f"Failed to ingest {filename}: {message}")

if __name__ == "__main__":
    target_dir = "Data/Knowledge"
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    preload_knowledge(target_dir)
