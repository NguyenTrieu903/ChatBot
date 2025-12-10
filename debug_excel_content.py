"""Script để debug và xem nội dung thực tế từ Excel files."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loaders.data_loader import load_excel_data, ALLOWED_PRODUCTS
import pandas as pd

print("\n" + "="*70)
print("🔍 DEBUG: XEM NỘI DUNG THỰC TẾ TỪ EXCEL")
print("="*70)

excel_files = [
    "data/traning.xlsx",
    "data/traning_new.xlsx"
]

for excel_file in excel_files:
    print(f"\n{'='*70}")
    print(f"📂 File: {excel_file}")
    print(f"{'='*70}")
    
    if not Path(excel_file).exists():
        print(f"❌ File không tồn tại: {excel_file}")
        continue
    
    try:
        df = load_excel_data(excel_file)
        
        # Tìm cột "Trả lời"
        answer_column = None
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(keyword in col_lower for keyword in ['trả lời', 'answer', 'câu trả lời', 'response']):
                answer_column = col
                break
        
        if not answer_column:
            answer_column = df.columns[-1]
        
        print(f"\n📋 Cột 'Trả lời': {answer_column}")
        print(f"📊 Tổng số dòng: {len(df)}")
        print(f"📋 Tất cả các cột: {df.columns.tolist()}")
        
        # Hiển thị một vài dòng có sản phẩm được phép - XEM TẤT CẢ CÁC CỘT
        print(f"\n📄 Một số dòng có sản phẩm được phép (XEM TẤT CẢ CÁC CỘT):")
        print("-" * 70)
        
        count = 0
        for idx, row in df.iterrows():
            answer_text = str(row.get(answer_column, '')).strip()
            
            if not answer_text or answer_text == 'nan':
                continue
            
            # Kiểm tra xem có sản phẩm nào trong text không
            found_product = None
            for product in ALLOWED_PRODUCTS:
                if product.lower() in answer_text.lower():
                    found_product = product
                    break
            
            if found_product:
                count += 1
                print(f"\n🔹 Dòng {idx + 1} - Sản phẩm: {found_product}")
                print(f"   {'='*68}")
                
                # Hiển thị TẤT CẢ các cột
                for col in df.columns:
                    col_value = str(row.get(col, '')).strip()
                    if col_value and col_value != 'nan':
                        print(f"\n   📌 Cột '{col}':")
                        print(f"      Độ dài: {len(col_value)} ký tự")
                        if len(col_value) <= 200:
                            print(f"      Nội dung: {col_value}")
                        else:
                            print(f"      Nội dung (200 ký tự đầu): {col_value[:200]}...")
                            print(f"      Nội dung (200 ký tự cuối): ...{col_value[-200:]}")
                
                print(f"   {'='*68}")
                
                if count >= 5:  # Hiển thị 5 ví dụ
                    break
        
        if count == 0:
            print("⚠️  Không tìm thấy sản phẩm được phép trong file này")
        
    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("✅ HOÀN TẤT")
print("="*70)

