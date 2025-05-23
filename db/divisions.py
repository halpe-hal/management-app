# db/divisions.py

from db.supabase_client import supabase
import logging

def get_divisions():
    try:
        res = supabase.table("divisions").select("*").order("id").execute()
        return [row["name"] for row in res.data] if res.data else []
    except Exception as e:
        logging.error(f"get_divisions error: {e}")
        return []

def update_division(id: int, new_name: str):
    try:
        supabase.table("divisions").update({"name": new_name}).eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"update_division error: {e}")
        return False

def delete_division(id: int):
    try:
        supabase.table("divisions").delete().eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_division error: {e}")
        return False

def get_division_records():
    try:
        res = supabase.table("divisions").select("*").order("id").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_division_records error: {e}")
        return []