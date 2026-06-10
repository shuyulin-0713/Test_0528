import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import traceback

class ExcelConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 轉檔工具 (B 欄結尾自動偵測)")
        self.root.geometry("450x650")
        
        self.file_path = ""
        self.sheet_vars = {} 

        # 1. 選擇檔案按鈕
        tk.Button(root, text="第一步：選擇 Excel 檔案", command=self.open_file, 
                  bg="#007bff", fg="white", pady=10, font=("微軟正黑體", 10, "bold")).pack(fill=tk.X, padx=20, pady=15)

        self.label_info = tk.Label(root, text="尚未選擇檔案", fg="gray")
        self.label_info.pack()

        # 2. 頁籤清單區 (含捲軸修正)
        frame_outer = tk.LabelFrame(root, text="第二步：勾選頁籤 (捲軸可滑動)")
        frame_outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(frame_outer, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(frame_outer, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 綁定捲軸區域
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        # 綁定滑鼠滾輪 (支援上下滑動)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 3. 開始轉換按鈕
        self.btn_run = tk.Button(root, text="第三步：開始轉換 (自動偵測 B 欄結尾)", command=self.run_convert, 
                                 bg="#28a745", fg="white", pady=10, state=tk.DISABLED, font=("微軟正黑體", 10, "bold"))
        self.btn_run.pack(fill=tk.X, padx=20, pady=20)

    def open_file(self):
        path = filedialog.askopenfilename(title="選擇 Excel 檔案", filetypes=[("Excel files", "*.xlsx *.xlsm *.xls")])
        if not path: return
        self.file_path = path
        self.label_info.config(text=f"已選擇：{os.path.basename(path)}", fg="black")
        
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.sheet_vars = {}

        try:
            xl = pd.ExcelFile(path)
            for s in xl.sheet_names:
                var = tk.BooleanVar(value=False)
                cb = tk.Checkbutton(self.scroll_frame, text=s, variable=var, wraplength=350, justify="left", font=("微軟正黑體", 10))
                cb.pack(anchor="w", padx=10, pady=5)
                self.sheet_vars[s] = var
            self.btn_run.config(state=tk.NORMAL)
            self.canvas.yview_moveto(0)
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取失敗：{e}")

    def run_convert(self):
        def clean_val(x):
            if pd.isna(x): return ""
            if isinstance(x, (float, int)):
                if float(x).is_integer(): return str(int(x))
                return str(x)
            s = str(x).strip()
            return s[:-2] if s.endswith('.0') else s

        results = []
        try:
            xl = pd.ExcelFile(self.file_path)
            for s_name, var in self.sheet_vars.items():
                if var.get():
                    full_df = pd.read_excel(xl, sheet_name=s_name, header=None, dtype=object)
                    
                    if "表頭" in s_name:
                        skip, start_col, end_limit = 1, 1, 11 
                        prefix = "EXP_H01"
                    elif "表身" in s_name:
                        skip, start_col, end_limit = 3, 1, 23 
                        prefix = "EXP_L01"
                    else:
                        skip, start_col, end_limit = 0, 0, full_df.shape[1]
                        prefix = "EXP"

                    actual_end = min(end_limit, full_df.shape[1])
                    df = full_df.iloc[skip:, start_col:actual_end]
                    
                    if not df.empty:
                        # 設定第一列為表頭
                        df.columns = df.iloc[0]
                        df = df.iloc[1:]
                        
                        # --- 核心邏輯：自動偵測 B 欄 (現在 df 的第一欄) 的結尾 ---
                        # 只要 B 欄是空的，就視為資料結束
                        mask = df.iloc[:, 0].apply(lambda x: pd.isna(x) or str(x).strip() == "")
                        
                        if mask.any():
                            # 取得第一個空白列的索引位置
                            first_empty_idx = df.index[mask][0]
                            # 只保留空白列之前的資料
                            df = df.loc[:first_empty_idx].iloc[:-1]
                        
                        # 清理多餘的空白欄位 (例如 W 欄沒資料就不抓)
                        df = df.dropna(axis=1, how='all')

                        if not df.empty:
                            df = df.map(clean_val) if hasattr(df, 'map') else df.applymap(clean_val)
                            out_name = f"{prefix}_{s_name}.txt"
                            save_path = os.path.join(os.path.dirname(self.file_path), out_name)
                            df.to_csv(save_path, sep='\t', index=False, header=True, encoding='utf-8-sig')
                            results.append(f"✅ {s_name}")

            messagebox.showinfo("完成", "\n".join(results) if results else "未選取任何有效頁籤")
        except Exception:
            messagebox.showerror("執行錯誤", traceback.format_exc())

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelConverter(root)
    root.mainloop()