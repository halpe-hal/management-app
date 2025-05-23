# db/all_sales.py

from db.supabase_client import supabase
from datetime import datetime
import logging

def get_sales(year: int, month: int, top_category: str) -> list:
    """指定された月・カテゴリの入金明細をページネーションで取得"""
    try:
        BATCH_SIZE = 1000
        all_data = []
        offset = 0

        while True:
            query = supabase.table("all_sales")\
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
                break

            offset += BATCH_SIZE

        return all_data
    except Exception as e:
        logging.error(f"get_sales error: {e}")
        return []

def add_sale(year: int, month: int, partner: str, detail: str, expected_amount: float, received_amount: float, payment: str, top_category: str, invoice_issued: bool, tax_rate: str) -> bool:
    """新しい入金データを追加"""
    try:
        supabase.table("all_sales").insert({
            "year": year,
            "month": month,
            "partner": partner,
            "detail": detail,
            "expected_amount": expected_amount,
            "received_amount": received_amount,
            "payment": payment,
            "invoice_issued": invoice_issued,
            "top_category": top_category,
            "tax_rate": tax_rate,
            "updated_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logging.error(f"add_sale error: {e}")
        return False

def delete_sale(sale_id: int) -> bool:
    """指定した入金データを削除"""
    try:
        supabase.table("all_sales").delete().eq("id", sale_id).execute()
        return True
    except Exception as e:
        logging.error(f"delete_sale error: {e}")
        return False

def update_sales_total(year: int, month: int, top_category: str) -> bool:
    """その月・事業部の入金データを tax_rate ごとに合計し all_sales_total に保存"""
    try:
        # 対象データ取得
        res = supabase.table("all_sales").select("*")\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)\
            .execute()

        data = res.data if res.data else []

        # tax_rate ごとに group by
        totals_by_tax = {}
        for row in data:
            tax = row.get("tax_rate", "売上10%")
            amount = row.get("received_amount", 0)
            totals_by_tax[tax] = totals_by_tax.get(tax, 0) + amount

        # 既存データ削除
        supabase.table("all_sales_total").delete()\
            .eq("year", year)\
            .eq("month", month)\
            .eq("top_category", top_category)\
            .execute()

        # 複数の tax_rate ごとに登録
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
        logging.error(f"update_sales_total error: {e}")
        return False
