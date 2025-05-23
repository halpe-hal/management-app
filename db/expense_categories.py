# db/expense_categories.py

from db.supabase_client import supabase
import logging

def get_expense_categories() -> list[str]:
    """登録済みカテゴリを sort_order 順に取得"""
    try:
        res = supabase.table("expense_categories")\
            .select("second_category, sort_order")\
            .order("sort_order").execute()
        if res.data:
            return [row["second_category"] for row in res.data if row.get("second_category")]
        return []
    except Exception as e:
        logging.error(f"get_expense_categories error: {e}")
        return []

def add_expense_category(category: str, is_fixed: bool = False) -> str:
    try:
        existing = supabase.table("expense_categories")\
            .select("second_category").eq("second_category", category).execute()
        if existing.data:
            return "duplicate"

        current = supabase.table("expense_categories")\
            .select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = current.data[0]["sort_order"] + 1 if current.data and current.data[0].get("sort_order") is not None else 0

        supabase.table("expense_categories")\
            .insert({
                "second_category": category,
                "sort_order": max_order,
                "is_fixed": is_fixed  # ← 追加
            }).execute()
        return "success"
    except Exception as e:
        logging.error(f"add_expense_category error: {e}")
        return "error"


def delete_expense_category(category: str) -> bool:
    try:
        supabase.table("expense_categories").delete().eq("second_category", category).execute()
        return True
    except Exception as e:
        logging.error(f"delete_expense_category error: {e}")
        return False

def update_expense_category_order(name_order_list: list[str]) -> bool:
    try:
        for index, name in enumerate(name_order_list):
            supabase.table("expense_categories")\
                .update({"sort_order": index})\
                .eq("second_category", name).execute()
        return True
    except Exception as e:
        logging.error(f"update_expense_category_order error: {e}")
        return False

def get_variable_expense_categories() -> list[str]:
    """変動費カテゴリ（is_fixed=False）だけ取得"""
    try:
        res = supabase.table("expense_categories")\
            .select("second_category, sort_order")\
            .eq("is_fixed", False)\
            .order("sort_order")\
            .execute()
        if res.data:
            return [row["second_category"] for row in res.data if row.get("second_category")]
        return []
    except Exception as e:
        logging.error(f"get_variable_expense_categories error: {e}")
        return []

def get_fixed_expense_categories() -> list[str]:
    """固定費カテゴリ（is_fixed=True）だけ取得"""
    try:
        res = supabase.table("expense_categories")\
            .select("second_category, sort_order")\
            .eq("is_fixed", True)\
            .order("sort_order")\
            .execute()
        if res.data:
            return [row["second_category"] for row in res.data if row.get("second_category")]
        return []
    except Exception as e:
        logging.error(f"get_fixed_expense_categories error: {e}")
        return []
