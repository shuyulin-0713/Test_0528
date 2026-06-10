import datetime
from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(r"D:\金洋\金洋_財報\年度匯率")
BASE_DIR.mkdir(parents=True, exist_ok=True)

CURRENCIES = ["USD", "CNY", "JPY", "EUR"]


def fetch_exchange_rate(currency, start_date, end_date):
    url = "https://api.finmindtrade.com/api/v3/data"
    params = {
        "dataset": "TaiwanExchangeRate",
        "data_id": currency,
        "date": start_date,
        "end_date": end_date,
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json().get("data", [])
        df = pd.DataFrame(data)
        if df.empty:
            return df
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"⚠ API 請求失敗 ({currency}): {e}")
        return pd.DataFrame()


def load_existing_sheet(excel_path, sheet_name):
    if not excel_path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception:
        return pd.DataFrame()


def merge_no_duplicate(existing_df, new_df):
    # 如果兩個都是空的，回傳空表格
    if existing_df.empty and new_df.empty:
        return pd.DataFrame()
    # 如果某一邊是空的，直接回傳另一邊的完整拷貝
    if existing_df.empty:
        return new_df.copy()
    if new_df.empty:
        return existing_df.copy()

    existing_df = existing_df.copy()
    new_df = new_df.copy()

    # 合併兩者
    merged = pd.concat([existing_df, new_df], ignore_index=True)

    # 智慧去重邏輯：
    # 建議使用 keep="last" (保留最新)，這樣如果台銀當天傍晚更新了最終收盤匯率，才能刷新掉早上的暫時匯率。
    # 如果你堅持只要重複就不動它，可以改回 keep="first"。
    merged = merged.drop_duplicates(subset=["date"], keep="last")

    # 排序：習慣上最新日期在最上面（由新到舊），看財務報表比較直覺
    merged = merged.sort_values("date", ascending=False).reset_index(drop=True)
    return merged


def main():
    year_text = input("請輸入要下載的年度，例如 2026：").strip()
    if not year_text.isdigit() or len(year_text) != 4:
        print("年度輸入錯誤，請輸入4位數字，例如 2026")
        return

    year = int(year_text)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    # 檔案名稱增加年度
    excel_path = BASE_DIR / f"台灣銀行_歷史匯率_{year}_USD_CNY_JPY_EUR.xlsx"

    output_data = {}

    for currency in CURRENCIES:
        print(f"正在處理 {currency} ...")

        # 1. 不管三七二十一，先載入已經存好的舊資料（防蒸發保護機制）
        existing_df = load_existing_sheet(excel_path, currency)

        # 2. 去線上抓最新資料
        new_df = fetch_exchange_rate(currency, start_date, end_date)

        if new_df.empty:
            print(f"  提示：線上未提供新資料，將保留既有歷史資料。")

        # 3. 合併與智慧去重
        final_df = merge_no_duplicate(existing_df, new_df)

        if not final_df.empty:
            # 格式化日期移除 Excel 討厭的 00:00:00 時分秒
            final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")
            output_data[currency] = final_df

    # 4. 統一寫入同一張 Excel 不同的工作表 (Sheet)
    if not output_data:
        print("❌ 沒有任何可輸出的資料")
        return

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for currency, df in output_data.items():
            df.to_excel(writer, sheet_name=currency, index=False)
            print(f"➔ 成功儲存 Sheet 【{currency}】 (共 {len(df)} 筆)")

    print(f"\n🎉 任務成功完成！檔案路徑：\n{excel_path}")


if __name__ == "__main__":
    main()