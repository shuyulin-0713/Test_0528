import os
import re
import glob
import numpy as np

try:
    import easyocr
    import pdfplumber
except ImportError:
    print("請先安裝必備套件: pip install easyocr pdfplumber")
    exit()

# 初始化 EasyOCR 引擎
print("正在初始化 EasyOCR 辨識引擎，請稍候...")
reader = easyocr.Reader(['ch_tra', 'en'], gpu=False)

def extract_po_info_from_pdf(pdf_path):
    """
    雙區精準特徵比對版：同時掃描右上方與最底部空白區，利用特定字形容錯，徹底根除雜訊誤判。
    """
    po_number = None
    vendor_name = ""
    is_supplement = False
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return None
            
            first_page = pdf.pages[0]
            width = first_page.width
            height = first_page.height
            
            # =========================================================
            # 區塊一：左上半部基本資訊區 (寬度 0~80%, 高度 0~55%) -> 專抓單號與廠商
            # =========================================================
            crop_main_bbox = (0, 0, width * 0.8, height * 0.55)
            main_page = first_page.crop(crop_main_bbox)
            img_main = main_page.to_image(resolution=300)
            img_main_np = np.array(img_main.original)
            
            main_results = reader.readtext(img_main_np, detail=0)
            main_text = " ".join(main_results)
            
            # =========================================================
            # 區塊二：右上角手寫空白區 (寬度 65%~100%, 高度 12%~45%)
            # =========================================================
            crop_top_right = (width * 0.65, height * 0.12, width, height * 0.45)
            tr_page = first_page.crop(crop_top_right)
            img_tr = tr_page.to_image(resolution=300) 
            img_tr_np = np.array(img_tr.original)
            tr_text = "".join(reader.readtext(img_tr_np, detail=0)).replace(" ", "")
            
            # =========================================================
            # 區塊三：最底部手寫備註區 (寬度 50%~100%, 高度 85%~100%)
            # =========================================================
            crop_bottom = (width * 0.5, height * 0.85, width, height)
            bt_page = first_page.crop(crop_bottom)
            img_bt = bt_page.to_image(resolution=300)
            img_bt_np = np.array(img_bt.original)
            bt_text = "".join(reader.readtext(img_bt_np, detail=0)).replace(" ", "")
            
            filename = os.path.basename(pdf_path)
            
            # 【核心清理】排除原本右上方就有的印刷字，避免干擾
            tr_text_cleaned = re.sub(r'(單據日期|公司傳真|\d{4}/\d{2}/\d{2}|\d{2}-\d{4}-\d{4}|頁次)', '', tr_text)
            
            print(f"--- [{filename}] 辨識報告 ---")
            print(f"  [右上區文字]: '{tr_text_cleaned}'")
            print(f"  [最底區文字]: '{bt_text}'")
            
            # 【判斷 1】提取採購單號
            po_match = re.search(r'\b48\d{8}\b', main_text)
            if po_match:
                po_number = po_match.group(0).strip()
            else:
                backup_po = re.search(r'\b\d{10}\b', main_text)
                if backup_po:
                    po_number = backup_po.group(0).strip()

            # 【判斷 2】提取廠商名稱前 4 個字
            vendor_match = re.search(r'廠商名稱\s*[:：\s]*(.*?)(?:\s|$)', main_text)
            if vendor_match:
                full_vendor = vendor_match.group(1).strip()
                full_vendor = re.sub(r'[:：\s\-]', "", full_vendor)
                vendor_name = full_vendor[:4]
            else:
                known_vendors = [
                    '放伴智能', '台灣順豐', '能騏', '防潮家', '昌德', '良成', 
                    '晉茂', '昱捷', '駿豪', '秉宸', '海天', '六豐', '恩斯', 
                    '騏達', '町洋', '比利迦', '威倫', '寶信', '德懋'
                ]
                for kv in known_vendors:
                    if kv in main_text:
                        vendor_name = kv
                        break
            
            if not vendor_name:
                vendor_name = "未知廠商"
            
            if "台灣順豐" in vendor_name or "順豐速運" in vendor_name:
                vendor_name = "順豐"
            elif "町洋企業" in vendor_name:
                vendor_name = "町洋"

            # 【判斷 3】精密補單判定 (利用關鍵容錯字集進行交叉比對)
            # 合併兩個可能出現手寫字的區域
            combined_target_text = tr_text_cleaned + bt_text
            
            # 定義手寫「補單」極度容易被認錯的字元集
            supplement_keywords = ['補', '單', '布', '車', '革', '草', '畢', '軍', '目', '田', '早', '痛']
            
            # 計算這些特徵字在區塊中一共出現了幾次
            match_count = sum(1 for char in combined_target_text if char in supplement_keywords)
            
            # 只有當區域內包含「補」字，或者至少出現 2 個以上的容錯特徵字，才判定為補單（完美過濾單一雜訊）
            if "補" in combined_target_text or match_count >= 2:
                is_supplement = True
                print(f"  --> [判定結果]: 發現明確手寫補單特徵，判定為【補單】。")
            else:
                is_supplement = False
                print(f"  --> [判定結果]: 無手寫字，判定為【正常單】。")
                
            print("-" * 50)
            return po_number, vendor_name, is_supplement
                
    except Exception as e:
        print(f"處理文件 {os.path.basename(pdf_path)} 時出錯: {e}")
    
    return None

def rename_pdfs_to_po(folder_path):
    if not os.path.exists(folder_path):
        print(f"錯誤：找不到指定的資料夾路徑 -> {folder_path}")
        return

    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        print("未在指定路徑找到任何 PDF 文件。")
        return

    print(f"\n目標資料夾: {folder_path}")
    print(f"找到 {len(pdf_files)} 個 PDF 文件，開始執行【智慧防誤判更名】...\n")
    success_count = 0
    
    for pdf_path in pdf_files:
        old_name = os.path.basename(pdf_path)
        
        info = extract_po_info_from_pdf(pdf_path)
        
        if info and info[0]:
            po_num, v_name, is_supp = info
            
            if is_supp:
                new_name = f"{v_name}-{po_num}-補.pdf"
            else:
                new_name = f"{v_name}-{po_num}.pdf"
                
            new_path = os.path.join(folder_path, new_name)
            
            counter = 1
            while os.path.exists(new_path):
                if pdf_path == new_path:
                    break
                if is_supp:
                    new_name = f"{v_name}-{po_num}-補_{counter}.pdf"
                else:
                    new_name = f"{v_name}-{po_num}_{counter}.pdf"
                new_path = os.path.join(folder_path, new_name)
                counter += 1
                
            if pdf_path == new_path:
                continue
                
            try:
                os.rename(pdf_path, new_path)
                print(f"[V] 更名成功: {old_name} -> {new_name}\n")
                success_count += 1
            except Exception as e:
                print(f"[X] 重命名失敗 {old_name}: {e}\n")
        else:
            print(f"[?] 無法從 {old_name} 辨識出有效採購單號，保持原狀。\n")

    print(f"\n處理完成！本次成功幫您更名/校正了 {success_count} / {len(pdf_files)} 個檔案。")

if __name__ == "__main__":
    target_directory = r"D:\shuyu.lin\Documents\採購單PDF"
    rename_pdfs_to_po(target_directory)