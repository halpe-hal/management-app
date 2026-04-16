# db/brands.py

from db.supabase_client import supabase
import logging

def get_brands():
    """ブランド名の一覧を sort_order 順に返す"""
    try:
        res = supabase.table("brands").select("*").order("sort_order").execute()
        return [row["name"] for row in res.data] if res.data else []
    except Exception as e:
        logging.error(f"get_brands error: {e}")
        return []

def get_brand_records():
    """ブランドのレコード一覧を sort_order 順に返す"""
    try:
        res = supabase.table("brands").select("*").order("sort_order").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_brand_records error: {e}")
        return []

def add_brand(name: str) -> str:
    """ブランドを新規登録する"""
    try:
        existing = supabase.table("brands").select("name").eq("name", name).execute()
        if existing.data:
            return "duplicate"

        current = supabase.table("brands").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = current.data[0]["sort_order"] + 1 if current.data and current.data[0].get("sort_order") is not None else 0

        supabase.table("brands").insert({"name": name, "sort_order": max_order}).execute()
        return "success"
    except Exception as e:
        logging.error(f"add_brand error: {e}")
        return "error"

def delete_brand(id: int) -> bool:
    try:
        supabase.table("brands").delete().eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_brand error: {e}")
        return False

def update_brand_order(brand_records: list) -> bool:
    """並び順を更新する"""
    try:
        for index, row in enumerate(brand_records):
            supabase.table("brands").update({"sort_order": index}).eq("id", row["id"]).execute()
        return True
    except Exception as e:
        logging.error(f"update_brand_order error: {e}")
        return False
