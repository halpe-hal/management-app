# db/account_items.py

from db.supabase_client import supabase
import logging

def get_account_items() -> list:
    try:
        res = supabase.table("account_items").select("*").order("name").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_account_items error: {e}")
        return []

def save_account_item(name: str) -> str:
    try:
        existing = supabase.table("account_items").select("*").eq("name", name).execute()
        if existing.data:
            return "duplicate"

        supabase.table("account_items").insert({"name": name}).execute()
        return "success"
    except Exception as e:
        logging.error(f"save_account_item error: {e}")
        return "error"


def delete_account_item(item_id: int) -> bool:
    try:
        supabase.table("account_items").delete().eq("id", item_id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_account_item error: {e}")
        return False
