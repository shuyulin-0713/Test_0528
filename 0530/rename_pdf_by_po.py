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
    極速優化版：裁切關鍵區塊，精準提取採購單號、廠商名稱與補單狀態
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
            
            # --- 速度優化 1：裁切上方 35% 區塊抓取 單號與廠商 ---
            crop_top_bbox = (0, 0, width, height * 0.35)
            top_page = first_page.crop(crop_top_bbox)
            img_top = top_page.to_image(resolution=300)
            img_top_np = np.array(img_top.original)
            
            # 辨識上方區塊
            top_results = reader.readtext(img_top_np, detail=0)
            top_text = " ".join(top_results)
            
            # --- 速度優化 2：裁切下方 15% 區塊檢查是否有手寫「補單」 ---
            crop_bottom_bbox = (0, height * 0.85, width, height)
            bottom_page = first_page.crop(crop_bottom_bbox)
            img_bottom = bottom_page.to_image(resolution=300)
            img_bottom_np = np.array(img_bottom.original)
            
            # 辨識下方區塊
            bottom_results = reader.readtext(img_bottom_np, detail=0)
            bottom_text = " ".join(bottom_results)
            
            # 【判斷 1】提取採購單號（優先找10碼純數字）
            po_match = re.search(r'\b48\d{8}\b', top_text)
            if po_match:
                po_number = po_match.group(0).strip()
            else:
                # 備用：若沒精準抓到 48 開頭，抓任意 10 碼
                backup_po = re.search(r'\b\d{10}\b', top_text)
                if backup_po:
                    po_number = backup_po.group(0).strip()

            # 【判斷 2】提取廠商名稱前 4 個字
            # 尋找「廠商名稱」欄位後面的文字
            vendor_match = re.search(r'廠商名稱\s*[:：\s]*(.*?)(?:\s|$)', top_text)
            if vendor_match:
                full_vendor = vendor_match.group(1).strip()
                # 去除可能誤抓的符號，並擷取前 4 個字
                full_vendor = re.sub(r'[:：\s\-]', "", full_vendor)
                vendor_name = full_vendor[:4]
            else:
                # 備用方案：如果在欄位後沒抓到，依據常見廠商關鍵字比對
                known_vendors = ['放伴智能', '台灣順豐', '能騏', '防潮家', '昌德', '良成', '晉茂', '昱捷', '駿豪', '秉宸', '海天', '六豐', '恩斯', '騏達']
                for kv in known_vendors:
                    if kv in top_text:
                        vendor_name = kv
                        break
            
            # 如果還是完全找不到廠商名稱，給予預設
            if not vendor_name:
                vendor_name = "未知廠商"
            # 若廠商名稱包含「台灣順豐」，依據您的範例簡化成「順豐」
            if "台灣順豐" in vendor_name or "順豐速運" in vendor_name:
                vendor_name = "順豐"

            # 【判斷 3】檢查是否為補單
            if "補" in bottom_text or "單" in bottom_text or "補" in top_text:
                is_supplement = True
                
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
    print(f"找到 {len(pdf_files)} 個 PDF 文件，開始執行【智慧格式改名】...\n")
    success_count = 0
    
    for pdf_path in pdf_files:
        old_name = os.path.basename(pdf_path)
        
        # 解析 PDF 資訊
        info = extract_po_info_from_pdf(pdf_path)
        
        if info and info[0]:  # 必須有採購單號才改名
            po_num, v_name, is_supp = info
            
            # 根據規則組合新檔名
            # 規則：廠商名稱前4個字-採購單號-補 (若無補單則無後綴)
            if is_supp:
                new_name = f"{v_name}-{po_num}-補.pdf"
            else:
                new_name = f"{v_name}-{po_num}.pdf"
                
            new_path = os.path.join(folder_path, new_name)
            
            # 處理檔名重複
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
                print(f"[-] 文件 {old_name} 檔名已符合規範，跳過。")
                continue
                
            try:
                os.rename(pdf_path, new_path)
                print(f"[V] 智慧更名成功: {old_name} \n    -> {new_name}")
                success_count += 1
            except Exception as e:
                print(f"[X] 重命名失敗 {old_name}: {e}")
        else:
            print(f"[?] 無法從 {old_name} 頂部區塊辨識出採購單號，保持原狀。")

    print(f"\n處理完成！本次成功幫您更名 {success_count} / {len(pdf_files)} 個檔案。")

if __name__ == "__main__":
    target_directory = r"D:\shuyu.lin\Documents\採購單PDF"
    rename_pdfs_to_po(target_directory)
