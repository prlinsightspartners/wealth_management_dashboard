from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

supabase_url: str = os.getenv("SUPABASE_URL")
supabase_key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)
print("Supabase client created successfully.")


# Test the connection by fetching the current user (should be None for anon key)
try:
    test = supabase.schema("asset_management").table("Clients").select("*").limit(1).execute()
    # test = supabase.table("options_chain").select("*").limit(1).execute()
    print("Test query executed successfully:", test)
except Exception as e:
    print("Error executing test query:", e)