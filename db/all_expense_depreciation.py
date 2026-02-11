# db/all_expense_depreciation.py

from db.supabase_client import supabase
from datetime import datetime
import logging

def get_expenses_depreciation(year: int, month: int, top_category: str) -> list:
    """指定された月・カテゴリの出金明細をページネーションで取得"""
    try:
        BATCH_SIZE = 1000
        all_data = []
        offset = 0

        while True:
            query = supabase.table("all_expense_depreciation")\
                .select("*")\
                .eq("year", year)\
                .eq("month", month)\
                .eq("top_category", top_category)\
                .order("id")\
                .range(offset, offset + BATCH_SIZE - 1)

            res = query.execute()
            batch = res.data or []
            all_data.extend(batch)

            if len(batch) < BATCH_SIZE:
                break  # 最後まで到達

            offset += BATCH_SIZE

        return all_data
    except Exception as e:
        logging.error(f"get_expenses error: {e}")
        return []

def add_expense_depreciation(year: int, month: int, partner: str, account: str, detail: str, payment: str, cost: float, second_category: str, top_category: str) -> bool:
    """新しい出金データを追加"""
    try:
        supabase.table("all_expense_depreciation").insert({
            "year": year,
            "month": month,
            "partner": partner,
            "account": account,
            "detail": detail,
            "payment": payment,
            "cost": cost,
            "second_category": second_category,
            "top_category": top_category,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logging.error(f"add_expense error: {e}")
        return False

def delete_expense_depreciation(expense_id: int) -> bool:
    """指定した出金データを削除"""
    try:
        supabase.table("all_expense_depreciation").delete().eq("id", expense_id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_expense error: {e}")
        return False

def update_expense_totals_depreciation_by_category(year: int, month: int, second_category: str, top_category: str) -> bool:
    """指定カテゴリの出金データを合計してall_expense_total_depreciationに保存"""
    try:
        # 指定条件で該当データ取得
        res = supabase.table("all_expense_depreciation").select("*")\
            .eq("year", year).eq("month", month)\
            .eq("second_category", second_category).eq("top_category", top_category).execute()
        if not res.data:
            return True
        else:
            total_cost = sum(row.get("cost", 0) for row in res.data)

        # 既存データ削除
        supabase.table("all_expense_total_depreciation").delete()\
            .eq("year", year).eq("month", month)\
            .eq("second_category", second_category).eq("top_category", top_category).execute()

        # 登録
        supabase.table("all_expense_total_depreciation").insert({
            "year": year,
            "month": month,
            "second_category": second_category,
            "top_category": top_category,
            "total_cost": total_cost,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logging.error(f"[update_expense_totals_by_category] Error: {e}")
        return False
