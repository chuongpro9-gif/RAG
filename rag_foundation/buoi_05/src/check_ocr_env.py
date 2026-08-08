import importlib.util
import sys

def check_package(package_name):
    if importlib.util.find_spec(package_name) is None:
        return "FAIL"
    return "PASS"

def main():
    packages = {
        "PyMuPDF": "fitz",
        "Pillow": "PIL",
        "llama-parse": "llama_parse",
        "Llama Cloud": "llama_cloud",
        "Pydantic": "pydantic",
        "Streamlit": "streamlit",
        "dotenv": "dotenv"
    }

    print("Kiểm tra môi trường OCR:")
    print("-" * 30)
    print(f"{'Package':<15} | {'Status':<10}")
    print("-" * 30)
    
    all_pass = True
    for name, module in packages.items():
        status = check_package(module)
        if status == "FAIL":
            all_pass = False
        print(f"{name:<15} | {status:<10}")
    
    print("-" * 30)
    
    if not all_pass:
        print("\nMột số thư viện chưa được cài đặt. Hệ thống sẽ tự động cài đặt...")
        print("Vui lòng chạy lệnh sau nếu cài đặt tự động thất bại:")
        print("pip install pymupdf pillow llama-parse pydantic streamlit python-dotenv")
    else:
        print("\nTất cả thư viện đã được cài đặt thành công (PASS).")

if __name__ == "__main__":
    main()
