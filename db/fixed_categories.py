# db/fixed_categories.py

from db.supabase_client import supabase
from datetime import datetime
import logging
from db.account_items import get_account_items
from decimal import Decimal
import streamlit as st


def get_fixed_categories() -> list:
    """登録されているすべての固定費項目を取得"""
    try:
        res = supabase.table("fixed_categories").select("*").execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_fixed_categories error: {e}")
        return []

def apply_fixed_expenses(year: int, month: int, selected_top_category: str) -> bool:
    """
    指定された Supabase 上の top_category（カフェ/広告/全体）に対応する固定費を取得し、
    all_expense テーブルに、second_category（家賃・その他固定費・融資返済）として保存する。
    """
    from db.all_expense import get_expenses  # 循環import防止

    try:
        fixed_items = get_fixed_categories()
        filtered = [f for f in fixed_items if f.get("top_category") == selected_top_category]

        existing = get_expenses(year, month, selected_top_category)
        existing_set = set(
            (e["partner"], e["account"], e["detail"], float(e["cost"]))
            for e in existing
        )

        new_rows = []
        for row in filtered:
            key = (row["partner"], row["account"], row["detail"], float(row["cost"]))
            if key not in existing_set:
                new_rows.append({
                    "year": year,
                    "month": month,
                    "partner": row["partner"],
                    "account": row["account"],
                    "detail": row["detail"],
                    "payment": row["payment"],
                    "cost": row["cost"],
                    "second_category": row["second_category"],
                    "top_category": row["top_category"],
                    "updated_at": datetime.now().isoformat()
                })

        if new_rows:
            supabase.table("all_expense").insert(new_rows).execute()

        return True
    except Exception as e:
        logging.error(f"apply_fixed_expenses error: {e}")
        return False



def save_fixed_category(partner: str, account: str, detail: str, payment: str, cost: float, top_category: str, second_category: str) -> str:
    try:
        existing = supabase.table("fixed_categories") \
            .select("*") \
            .eq("partner", partner) \
            .eq("account", account) \
            .eq("detail", detail) \
            .eq("top_category", top_category) \
            .execute()

        if existing.data:
            return "duplicate"

        supabase.table("fixed_categories").insert({
            "partner": partner,
            "account": account,
            "detail": detail,
            "payment": payment,
            "cost": str(Decimal(cost)),
            "top_category": top_category,
            "second_category": second_category,
            "updated_at": datetime.now().isoformat()
        }).execute()

        return "success"
    except Exception as e:
        logging.error(f"save_fixed_category error: {e}")
        st.exception(e)
        return "error"

def delete_fixed_category(fixed_id: int) -> bool:
    """固定費項目を削除"""
    try:
        supabase.table("fixed_categories").delete().eq("id", fixed_id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_fixed_category error: {e}")
        return False


def update_fixed_category(id: int, field: str, value) -> bool:
    try:
        supabase.table("fixed_categories") \
            .update({field: value, "updated_at": datetime.now().isoformat()}) \
            .eq("id", id) \
            .execute()
        return True
    except Exception as e:
        logging.error(f"update_fixed_category error: {e}")
        return False

