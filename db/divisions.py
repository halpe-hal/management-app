# db/divisions.py

from db.supabase_client import supabase
import logging

def get_divisions():
    try:
        # sort_order 順に取得
        res = supabase.table("divisions").select("*").order("sort_order").execute()
        return [row["name"] for row in res.data] if res.data else []
    except Exception as e:
        logging.error(f"get_divisions error: {e}")
        return []

def add_division(name: str) -> str:
    """新規事業部を登録し、sort_orderの最大値+1を設定する"""
    try:
        existing = supabase.table("divisions").select("name").eq("name", name).execute()
        if existing.data:
            return "duplicate"

        current = supabase.table("divisions").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = current.data[0]["sort_order"] + 1 if current.data and current.data[0].get("sort_order") is not None else 0

        supabase.table("divisions").insert({"name": name, "sort_order": max_order}).execute()
        return "success"
    except Exception as e:
        logging.error(f"add_division error: {e}")
        return "error"

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
        # sort_order 順に取得
        res = supabase.table("divisions").select("*").order("sort_order").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_division_records error: {e}")
        return []

def update_division_order(division_records: list[dict]) -> bool:
    """並び順を更新する"""
    try:
        for index, row in enumerate(division_records):
            supabase.table("divisions").update({"sort_order": index}).eq("id", row["id"]).execute()
        return True
    except Exception as e:
        logging.error(f"update_division_order error: {e}")
        return False
