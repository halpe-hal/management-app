# db/expense_targets.py

from db.supabase_client import supabase
import logging
from datetime import datetime

def get_expense_targets():
    """全ての事業部の目標比率を取得（リスト形式で返す）"""
    try:
        response = supabase.table("expense_targets").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        logging.error(f"get_expense_targets error: {e}")
        return []

def get_expense_target_by_top_category(top_category: str):
    """特定の事業部の目標比率を取得（辞書形式）"""
    try:
        response = supabase.table("expense_targets").select("*").eq("top_category", top_category).limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logging.error(f"get_expense_target_by_top_category error: {e}")
        return None

def upsert_expense_target(payload: dict):
    """
    目標比率の登録または更新。
    payload には以下の構造を含むこと：
    {
        "top_category": str,
        "cost_rate": float,
        "labor_rate": float,
        "fl_rate": float,
        "misc_rate": float,
        "utility_rate": float,
        "other_fixed_rate": float,
        "rent_rate": float,
        "flr_rate": float,
        "first_op_profit_rate": float
    }
    """
    try:
        # 既存レコードの有無をチェック
        existing = get_expense_target_by_top_category(payload["top_category"])

        if existing:
            supabase.table("expense_targets").update({
                **payload,
                "updated_at": datetime.now().isoformat()
            }).eq("id", existing["id"]).execute()
        else:
            supabase.table("expense_targets").insert({
                **payload,
                "updated_at": datetime.now().isoformat()
            }).execute()
        return True
    except Exception as e:
        logging.error(f"upsert_expense_target error: {e}")
        return False
