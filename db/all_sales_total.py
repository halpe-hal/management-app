# db/all_sales_total.py

from db.supabase_client import supabase
from datetime import datetime
import logging

def save_sales_totals(year: int, month: int, top_category: str, totals_by_tax: dict) -> bool:
    """
    税率ごとの入金合計を all_sales_total テーブルに保存（上書き）
    totals_by_tax: {"売上10%": 100000, "売上8%": 30000, ...}
    """
    try:
        # 既存データ削除
        supabase.table("all_sales_total").delete()\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)\
            .execute()

        # 各税率ごとに insert
        for tax_rate, total_amount in totals_by_tax.items():
            supabase.table("all_sales_total").insert({
                "year": year,
                "month": month,
                "top_category": top_category,
                "tax_rate": tax_rate,
                "total_amount": total_amount,
                "updated_at": datetime.now().isoformat()
            }).execute()

        return True
    except Exception as e:
        logging.error(f"save_sales_totals error: {e}")
        return False

def get_sales_totals(year: int, month: int, top_category: str, tax_rate: str = None) -> float:
    """
    入金合計を取得（tax_rateを指定すればその税率のみ、指定しなければ全合計）
    """
    try:
        query = supabase.table("all_sales_total")\
            .select("total_amount")\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)

        if tax_rate:
            query = query.eq("tax_rate", tax_rate)

        res = query.execute()
        if res.data:
            return sum(row["total_amount"] for row in res.data)
        else:
            return 0.0
    except Exception as e:
        logging.error(f"get_sales_totals error: {e}")
        return 0.0
    

def get_sales_totals_batch(years: list, top_category: str) -> list:
    """
    複数年の全売上（税率ごと）を一括取得
    返り値は [{year, month, tax_rate, total_amount}, ...] のリスト
    """
    try:
        res = supabase.table("all_sales_total").select("*")\
            .in_("year", years).eq("top_category", top_category)\
            .execute()
        return res.data if res.data else []
    except Exception as e:
        logging.error(f"get_sales_totals_batch error: {e}")
        return []
    
def get_sales_totals_all(years: list) -> list:
    """全事業部の売上合計を対象年で一括取得（ページネーション対応）"""
    try:
        BATCH_SIZE = 1000
        all_data = []
        offset = 0

        while True:
            query = supabase.table("all_sales_total")\
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
        logging.error(f"get_sales_totals_all error: {e}")
        return []
