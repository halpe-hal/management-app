# db/default_partners.py

from db.supabase_client import supabase
from datetime import datetime
import logging

def get_default_partners() -> list:
    """登録されているすべてのデフォルト行を取得"""
    try:
        res = supabase.table("default_partners").select("*").order("id").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_default_partners error: {e}")
        return []

def save_default_partner(second_category: str, partner: str, account: str, detail: str, payment: str, top_category: str) -> str:
    """新しいデフォルト行を登録（重複チェックあり）"""
    try:
        existing = supabase.table("default_partners") \
            .select("*") \
            .eq("second_category", second_category) \
            .eq("partner", partner) \
            .eq("account", account) \
            .eq("detail", detail) \
            .eq("payment", payment) \
            .eq("top_category", top_category) \
            .execute()

        if existing.data:
            return "duplicate"

        supabase.table("default_partners").insert({
            "second_category": second_category,
            "partner": partner,
            "account": account,
            "detail": detail,
            "payment": payment,
            "top_category": top_category,
            "updated_at": datetime.now().isoformat()
        }).execute()

        return "success"
    except Exception as e:
        logging.error(f"save_default_partner error: {e}")
        return "error"

def update_default_partner(id: int, field: str, value) -> bool:
    """指定フィールドを更新"""
    try:
        supabase.table("default_partners").update({
            field: value,
            "updated_at": datetime.now().isoformat()
        }).eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"update_default_partner error: {e}")
        return False

def delete_default_partner(id: int) -> bool:
    """デフォルト行を削除"""
    try:
        supabase.table("default_partners").delete().eq("id", id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_default_partner error: {e}")
        return False

def get_default_partners_by_category(second_category: str, top_category: str) -> list:
    """カテゴリ（second_category）と事業部（top_category）に応じたデフォルト取引先一覧を取得"""
    try:
        res = supabase.table("default_partners") \
            .select("*") \
            .eq("second_category", second_category) \
            .eq("top_category", top_category) \
            .order("id") \
            .execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_default_partners_by_category error: {e}")
        return []
