import pandas as pd
import numpy as np

# -------------------------------------------------------------------------
# 1. 建立包含「姓名」與「座號」的班級原始資料
# -------------------------------------------------------------------------
np.random.seed(42)
num_students = 28

# 模擬 28 位學生的姓名清單（實際使用時，你可以換成你自己的學生姓名清單）
student_names = [
    "林書宇", "陳小明", "張美麗", "李大華", "王曉芬", "趙志強", "孫大文", "錢秀蘭", 
    "周杰倫", "蔡依林", "吳名氏", "鄭成功", "馮小剛", "陳大天", "許志安", "黃小琥", 
    "楊丞琳", "羅志祥", "周婷婷", "何明翰", "施建國", "廖美玲", "曾文雄", "洪淑芬", 
    "藍天翔", "白雲飛", "柳乘風", "葉孤城"
]

raw_data = {
    '座號': range(1, num_students + 1),
    '姓名': student_names[:num_students], # 綁定姓名
    '國文': np.random.choice([97.5, 90, 87.5, 82.5, 80, 77.5, 72.5, 70, 67.5, 62.5, 60, 52.5, 50, 47.5, 37.5, 32.5, 27.5, 25], num_students),
    '數學': np.random.randint(40, 101, num_students),
    '英語': np.random.randint(40, 101, num_students),
    '社會': np.random.randint(50, 101, num_students),
    '自然': np.random.randint(50, 101, num_students)
}
df_orig = pd.DataFrame(raw_data)

# 確保分數欄位為浮點數
columns_to_sort = ['國文', '數學', '英語', '社會', '自然']
for col in columns_to_sort:
    df_orig[col] = df_orig[col].astype(float)

df_orig['總分'] = df_orig[columns_to_sort].sum(axis=1)

# 2. 各科獨立遞減排序（建立底下的對照表，這部分不需要包含姓名）
all_columns = ['國文', '數學', '英語', '社會', '自然', '總分']
sorted_columns_data = {}
for col in all_columns:
    sorted_columns_data[col] = df_orig[col].sort_values(ascending=False).reset_index(drop=True)

rank_table = pd.DataFrame(sorted_columns_data)
rank_table.index = rank_table.index + 1  # 序位從 1 開始

# -------------------------------------------------------------------------
# 3. 定義劃黑框的樣式與文字大小
# -------------------------------------------------------------------------
def highlight_target_marks(df_data, target_scores):
    styles = pd.DataFrame('text-align: center; font-size: 16px; padding: 6px;', index=df_data.index, columns=df_data.columns)
    for col in df_data.columns:
        val_to_find = target_scores[col]
        mask = df_data[col] == val_to_find
        styles.loc[mask, col] = 'border: 3px solid #000000; font-weight: bold; background-color: #f5f5f5; text-align: center; font-size: 16px; padding: 6px;'
    return styles

# -------------------------------------------------------------------------
# 4. 🔴 在這裡自由指定你想輸出的學生座號 (例如要看 10 號學生的成績單)
# -------------------------------------------------------------------------
target_seat = 10  

# 取得該學生的得分數據與姓名
target_student = df_orig[df_orig['座號'] == target_seat].iloc[0]
target_name = target_student['姓名'] # 👈 自動抓取對應的姓名

# -------------------------------------------------------------------------
# 5. 格式化表格小數點
# -------------------------------------------------------------------------
styled_table = rank_table.style.format("{:.1f}").apply(
    lambda x: highlight_target_marks(rank_table, target_student), axis=None
)

# -------------------------------------------------------------------------
# 6. 輸出 HTML 網頁檔，並在灰色框內同步秀出【座號】與【姓名】
# -------------------------------------------------------------------------
html_header = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>個人成績落點通知單</title>
    <style>
        body {{ font-family: "Microsoft JhengHei", sans-serif; margin: 30px; line-height: 1.6; }}
        .report-header {{ text-align: center; margin-bottom: 25px; }}
        .student-info {{ background-color: #f9f9f9; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 18px; }}
        table {{ border-collapse: collapse; margin: 0 auto; }}
        th {{ background-color: #f2f2f2; font-size: 18px; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="report-header">
        <h2>福營國中學年度第二學期第三次段考</h2>
        <h1>🏆 成績分數落點通知單 🏆</h1>
    </div>
    
    <div class="student-info">
        📌 <b>目前查詢對象：</b> 
        <span style="font-size: 22px; color: #d9534f; font-weight: bold;">座號 {target_seat} 號 — {target_name}</span> 的成績單<br>
        📋 <b>個人實際得分：</b> 
        國文: {target_student['國文']:.1f}分 | 
        數學: {target_student['數學']:.1f}分 | 
        英語: {target_student['英語']:.1f}分 | 
        社會: {target_student['社會']:.1f}分 | 
        自然: {target_student['自然']:.1f}分 | 
        <b>總分: {target_student['總分']:.1f}分</b>
    </div>
    
    <p style="color: #666; font-size: 14px;">※ 註 1：下方每科成績分數皆由高而低獨立排列，<b>【  】粗黑框</b>內表示該座號學生的該科得分落點。</p>
    <hr>
    <br>
"""

html_footer = """
</body>
</html>
"""

final_html_content = html_header + styled_table.to_html() + html_footer

# 寫入檔案並自動開啟
with open("成績單.html", "w", encoding="utf-8") as f:
    f.write(final_html_content)

import os
os.system("start 成績單.html")
print(f"✅ 成功！座號 {target_seat} 號（{target_name}）的網頁成績單已生成並自動開啟。")
