from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

def test_supabase_storage():
    try:
        print(f"Connecting to Supabase at {SUPABASE_URL}...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        bucket_name = "uploads"
        test_filename = "test_connection.txt"
        test_content = b"Supabase Storage is working correctly for Autoride System!"
        
        print(f"Attempting to upload a test file to bucket '{bucket_name}'...")
        # Uploading to a 'test' folder in the bucket
        res = supabase.storage.from_(bucket_name).upload(
            path=f"test/{test_filename}",
            file=test_content,
            file_options={"content-type": "text/plain", "upsert": "true"}
        )
        
        print(f"SUCCESS! File uploaded. Response: {res}")
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(f"test/{test_filename}")
        print(f"Public URL: {public_url}")
        
    except Exception as e:
        print(f"FAILED! Error: {str(e)}")
        print("\nTIP: Make sure you have created a PUBLIC bucket named 'uploads' in your Supabase Dashboard.")

if __name__ == "__main__":
    test_supabase_storage()
