# db/all_expense_total.py

from db.supabase_client import supabase
from datetime import datetime
import logging

def save_expense_totals(year: int, month: int, top_category: str, totals: dict) -> bool:
    """カテゴリごとの出金合計をall_expense_totalテーブルに保存（上書き）"""
    try:
        # 既存データ削除（top_categoryも条件に含める）
        supabase.table("all_expense_total").delete()\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)\
            .execute()

        # 登録用データ作成
        payload = [
            {
                "year": year,
                "month": month,
                "top_category": top_category,
                "second_category": second_category,
                "total_cost": cost,
                "updated_at": datetime.now().isoformat()
            }
            for second_category, cost in totals.items()
        ]
        supabase.table("all_expense_total").insert(payload).execute()
        return True
    except Exception as e:
        logging.error(f"save_expense_totals error: {e}")
        return False

def get_expense_totals(year: int, month: int, top_category: str) -> dict:
    """指定年月・事業部のカテゴリ別出金合計を取得"""
    try:
        res = supabase.table("all_expense_total")\
            .select("*")\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)\
            .execute()
        return {row["second_category"]: row["total_cost"] for row in res.data} if res.data else {}
    except Exception as e:
        logging.error(f"get_expense_totals error: {e}")
        return {}
    
def get_expense_totals_batch(years: list, top_category: str) -> list:
    """
    複数年の全出金（second_categoryごと）を一括取得
    返り値は [{year, month, second_category, total_cost}, ...] のリスト
    """
    try:
        res = supabase.table("all_expense_total").select("*")\
            .in_("year", years).eq("top_category", top_category)\
            .execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_expense_totals_batch error: {e}")
        return []
    
def get_expense_totals_all(years: list) -> list:
    """全事業部の出金合計を対象年で一括取得（ページネーション対応）"""
    try:
        BATCH_SIZE = 1000
        all_data = []
        offset = 0

        while True:
            query = supabase.table("all_expense_total")\
                .select("*")\
                .in_("year", years)\
                .order("id")\
                .range(offset, offset + BATCH_SIZE - 1)

            res = query.execute()
            batch = res.data or []
            all_data.extend(batch)

            if len(batch) < BATCH_SIZE:
                break

            offset += BATCH_SIZE

        return all_data
    except Exception as e:
        logging.error(f"get_expense_totals_all error: {e}")
        return []
