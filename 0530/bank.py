import datetime
from pathlib import Path
import pandas as pd
import requests

BASE_DIR = Path(r"D:\金洋\金洋_財報\年度匯率")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# 台灣特殊的補班日或需要確保存在的日期清單
SPECIAL_WORKDAYS = ["2025-02-08"]


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
        
        # 智慧欄位名稱校正機制
        if "data_date" in df.columns:
            df = df.rename(columns={"data_date": "date"})
        elif "資料日期" in df.columns:
            df = df.rename(columns={"資料日期": "date"})
            
        df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        print(f"⚠ API 請求失敗 ({currency}): {e}")
        return pd.DataFrame()


def fetch_bot_month_quote_fallback(currency, target_date_str):
    try:
        target_dt = pd.to_datetime(target_date_str)
        year_month_str = target_dt.strftime("%Y-%m")
        date_slash_str = target_dt.strftime("%Y/%m/%d")

        url = f"https://rate.bot.com.tw/xrt/quote/{year_month_str}/{currency}"
        tables = pd.read_html(url)

        if tables:
            df_table = tables[0]
            df_table.columns = [
                col[0] if isinstance(col, tuple) else col
                for col in df_table.columns
            ]
            df_table.columns = [col.strip() for col in df_table.columns]

            date_col_name = (
                "掛牌日期" if "掛牌日期" in df_table.columns else df_table.columns[0]
            )
            df_table[date_col_name] = (
                df_table[date_col_name].astype(str).str.strip()
            )

            row = df_table[df_table[date_col_name] == date_slash_str]

            if not row.empty:
                cash_buy = row.iloc[0, 2]
                cash_sell = row.iloc[0, 3]
                spot_buy = row.iloc[0, 4]
                spot_sell = row.iloc[0, 5]

                fallback_data = {
                    "date": [target_dt],
                    "currency": [currency],
                    "cash_buy": [pd.to_numeric(cash_buy, errors="coerce")],
                    "cash_sell": [pd.to_numeric(cash_sell, errors="coerce")],
                    "spot_buy": [pd.to_numeric(spot_buy, errors="coerce")],
                    "spot_sell": [pd.to_numeric(spot_sell, errors="coerce")],
                }
                return pd.DataFrame(fallback_data)
    except Exception:
        pass
    return pd.DataFrame()


def get_manual_input_exchange_rate(currency, target_date_str):
    print(f"\n--------------------------------------------------")
    print(f"✍  [手動輸入提示] 程式無法自動取得 {target_date_str} 的 {currency} 匯率。")
    print(f"    請翻閱紙本或台銀網頁，手動輸入當天即期匯率：")
    print(f"--------------------------------------------------")
    
    while True:
        try:
            spot_buy_input = input(f" ✏ 請輸入 {target_date_str} {currency} [即期買入] 匯率: ").strip()
            spot_sell_input = input(f" ✏ 請輸入 {target_date_str} {currency} [即期賣出] 匯率: ").strip()
            
            spot_buy = float(spot_buy_input)
            spot_sell = float(spot_sell_input)
            break
        except ValueError:
            print("❌ 輸入格式錯誤！請輸入正確的數字（例如: 32.74）。請再試一次。")

    target_dt = pd.to_datetime(target_date_str)
    manual_data = {
        "date": [target_dt],
        "currency": [currency],
        "cash_buy": [None],
        "cash_sell": [None],
        "spot_buy": [spot_buy],
        "spot_sell": [spot_sell],
    }
    return pd.DataFrame(manual_data)


def calculate_financial_evaluation_rates(df_detail):
    """計算單一幣別的各項財務匯率指標（全面取消四捨五入，保留最完整精度）"""
    if df_detail.empty:
        return {}, pd.DataFrame()

    df = df_detail.copy()
    df["spot_buy"] = pd.to_numeric(df["spot_buy"], errors="coerce")
    df["spot_sell"] = pd.to_numeric(df["spot_sell"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])

    df["year_month"] = df["date"].dt.to_period("M")

    # 1. 加權平均匯率（即：年度評價匯率 = (買入年均 + 賣出年均) / 2）
    monthly_avg = df.groupby("year_month")[["spot_buy", "spot_sell"]].mean().reset_index()
    annual_buy_avg = monthly_avg["spot_buy"].mean()
    annual_sell_avg = monthly_avg["spot_sell"].mean()
    annual_evaluation_rate = (annual_buy_avg + annual_sell_avg) / 2

    # 2. R(月底評價匯率) -> 抓每月最後工作日之均價年平均
    idx_last_workday = df.groupby("year_month")["date"].idxmax()
    df_last_workdays = df.loc[idx_last_workday].copy()
    df_last_workdays["month_end_avg"] = (df_last_workdays["spot_buy"] + df_last_workdays["spot_sell"]) / 2
    r_month_end_evaluation_rate = df_last_workdays["month_end_avg"].mean()

    # 3. 期初與期末匯率：採第一個與最後一個工作日之(買入+賣出)平均匯率
    df_sorted = df.sort_values("date", ascending=True).reset_index(drop=True)
    
    if not df_sorted.empty:
        # 期初第一個工作日
        first_row = df_sorted.iloc[0]
        initial_rate = (first_row["spot_buy"] + first_row["spot_sell"]) / 2
        initial_date_str = first_row["date"].strftime("%m/%d")
        
        # 期末最後一個工作日
        last_row = df_sorted.iloc[-1]
        final_rate = (last_row["spot_buy"] + last_row["spot_sell"]) / 2
        final_date_str = last_row["date"].strftime("%m/%d")
    else:
        initial_rate, final_rate = 0.0, 0.0
        initial_date_str, final_date_str = "", ""

    # 🎯【修改點】各工作表側邊的小摘要表格：完全移除 round()，輸出最完整浮點數
    summary_data = {
        "項目": [
            "即期買入_年度平均 (各月平均之平均)",
            "即期賣出_年度平均 (各月平均之平均)",
            "★ 年度評價匯率 ((買入年均 + 賣出年均) / 2)",
            "--------------------------------------------------",
            "★ 期初匯率 (第1個工作日即期買賣平均)",
            "★ 期末匯率 (最後1個工作日即期買賣平均)",
            "★ R (月底評價匯率) (各月最後工作日均價之年平均)",
        ],
        "匯率計算結果": [
            annual_buy_avg,
            annual_sell_avg,
            annual_evaluation_rate,
            "",
            initial_rate,
            final_rate,
            r_month_end_evaluation_rate,
        ],
    }
    
    # 🎯【修改點】傳遞給彙總報告的數據亦取消四捨五入
    summary_metrics = {
        "annual_evaluation": annual_evaluation_rate,
        "initial_rate": initial_rate,
        "initial_date_label": f"期初匯率 ({initial_date_str} 均價)",
        "final_rate": final_rate,
        "final_date_label": f"期末匯率 ({final_date_str} 均價)",
        "r_month_end": r_month_end_evaluation_rate
    }
    
    return summary_metrics, pd.DataFrame(summary_data)


def main():
    print("==========================================================================")
    print("💡 提示：請留意下載年度是否有『假日補班日』？")
    print("         若有，請確認已將該日期加入程式上方的 SPECIAL_WORKDAYS 清單中。")
    print("==========================================================================")

    year_text = input("請輸入要下載的年度 (例如 2025 或 2026)：").strip()
    if not year_text.isdigit() or len(year_text) != 4:
        print("❌ 年度輸入錯誤，請輸入 4 位數字")
        return

    currency_input = input("請輸入需要抓取的幣別清單，用逗號隔開 (例如: USD, CNY, JPY, EUR)：").strip()
    if not currency_input:
        print("❌ 幣別輸入不可為空")
        return
    
    currencies = [c.strip().upper() for c in currency_input.replace("，", ",").split(",") if c.strip()]
    
    year = int(year_text)
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    currencies_str = "_".join(currencies)
    excel_path = BASE_DIR / f"台灣銀行_歷史匯率_{year}_{currencies_str}.xlsx"

    output_data = {}
    summary_data_dict = {}
    all_currency_summary_metrics = {}

    for currency in currencies:
        print(f"\n正在處理 {currency} ...")

        new_df = fetch_exchange_rate(currency, start_date, end_date)

        for special_day in SPECIAL_WORKDAYS:
            special_date_dt = pd.to_datetime(special_day)

            if special_date_dt.year == year:
                has_in_new = (not new_df.empty and special_date_dt in new_df["date"].values)

                if not has_in_new:
                    print(f"  🔍 偵測到新抓取資料中漏抓補班日 {special_day}，嘗試自網頁抓取...")
                    df_real_day = fetch_bot_month_quote_fallback(currency, special_day)

                    if not df_real_day.empty:
                        new_df = pd.concat([new_df, df_real_day], ignore_index=True)
                        print(f"  ➔ 🚀 自動抓取成功！已補回真實數據。")
                    else:
                        df_manual = get_manual_input_exchange_rate(currency, special_day)
                        new_df = pd.concat([new_df, df_manual], ignore_index=True)

        if not new_df.empty:
            new_df = new_df.drop_duplicates(subset=["date"], keep="last")
            final_df = new_df.sort_values("date", ascending=False).reset_index(drop=True)
        else:
            final_df = pd.DataFrame()

        if not final_df.empty:
            metrics, summary_df = calculate_financial_evaluation_rates(final_df)
            summary_data_dict[currency] = summary_df
            all_currency_summary_metrics[currency] = metrics

            final_df["date"] = final_df["date"].dt.strftime("%Y-%m-%d")
            output_data[currency] = final_df

    if not output_data:
        print("❌ 沒有任何可輸出的資料")
        return

    # 動態彙總報告結構
    summary_rows = []
    success_currencies = [c for c in currencies if c in all_currency_summary_metrics]
    if not success_currencies:
        print("❌ 所有的幣別都沒有成功產生計算指標")
        return
        
    sample_metrics = all_currency_summary_metrics[success_currencies[0]]
    lbl_initial = sample_metrics.get("initial_date_label", "期初匯率")
    lbl_final = sample_metrics.get("final_date_label", "期末匯率")

    summary_rows.append({"項目": "加權平均匯率 (年度評價匯率)"})
    summary_rows.append({"項目": lbl_initial})
    summary_rows.append({"項目": lbl_final})
    summary_rows.append({"項目": "R (月底評價匯率)"})
    
    df_report = pd.DataFrame(summary_rows)
    
    for currency in currencies:
        if currency in all_currency_summary_metrics:
            m = all_currency_summary_metrics[currency]
            df_report[currency] = [
                m["annual_evaluation"],
                m["initial_rate"],
                m["final_rate"],
                m["r_month_end"]
            ]

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_report.to_excel(writer, sheet_name="彙總報告", index=False)
        print("➔ 🚀 成功建立動態【彙總報告】工作表")
        
        for currency, df_detail in output_data.items():
            df_detail.to_excel(writer, sheet_name=currency, index=False)

            if currency in summary_data_dict:
                summary_data_dict[currency].to_excel(
                    writer, sheet_name=currency, startcol=8, index=False
                )
            print(f"➔ 成功儲存 Sheet 【{currency}】")

    print(f"\n🎉 任務完美完成！所有財務匯率指標皆保留最完整精度（無四捨五入）。檔案路徑：\n{excel_path}")


if __name__ == "__main__":
    main()