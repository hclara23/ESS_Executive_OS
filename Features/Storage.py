import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("ELIO_GCS_BUCKET", "elio-assets-eliopva")

def upload_to_elio_storage(local_path, blob_name):
    """Uploads a file to the Elio GCS bucket."""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        return True, f"gs://{BUCKET_NAME}/{blob_name}"
    except Exception as e:
        return False, str(e)

def list_elio_documents():
    """Lists all files in the Elio GCS bucket."""
    try:
        client = storage.Client()
        blobs = client.list_blobs(BUCKET_NAME)
        return [blob.name for blob in blobs]
    except Exception as e:
        print(f"Storage List Error: {e}")
        return []

def delete_elio_document(blob_name):
    """Deletes a file from the Elio GCS bucket."""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except Exception as e:
        print(f"Storage Delete Error: {e}")
        return False
