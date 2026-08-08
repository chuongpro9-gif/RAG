import streamlit as st
import json
import os
import sys
import pandas as pd
import altair as alt

# Thêm thư mục src vào path để import logic chunking
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.append(src_path)
import ocr_chunking

# -----------------
# CẤU HÌNH TRANG
# -----------------
st.set_page_config(page_title="RAG Foundation - Buổi 05", layout="wide", page_icon="🔍")

# CSS tùy chỉnh để làm giao diện đẹp hơn (không copy hoàn toàn mà lấy cảm hứng)
st.markdown("""
<style>
    .main-header {
        background-color: #1E3A8A;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        margin-bottom: 0px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# -----------------
# HÀM HỖ TRỢ
# -----------------
def load_json(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "output", filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_raw_text():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "output", "raw_text.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_spec():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "SPEC_buoi_05.md")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Không tìm thấy file SPEC."

def save_json(data, filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_stats(chunks):
    if not chunks:
        return {"count": 0, "min": 0, "max": 0, "avg": 0}
    lengths = [len(c["text"]) for c in chunks]
    return {
        "count": len(chunks),
        "min": min(lengths),
        "max": max(lengths),
        "avg": round(sum(lengths) / len(lengths), 1)
    }

# -----------------
# SIDEBAR
# -----------------
with st.sidebar:
    st.header("⚙️ Cấu hình Luồng Xử Lý")
    st.markdown("**Chọn tài liệu PDF cần phân tích:**")
    
    # List files in datademo
    demo_dir = os.path.join(os.path.dirname(__file__), "datademo")
    pdf_files = [f for f in os.listdir(demo_dir) if f.endswith('.pdf')] if os.path.exists(demo_dir) else []
    selected_pdf = st.selectbox("Tài liệu:", options=pdf_files if pdf_files else ["Không có file PDF"])
    
    st.divider()
    
    st.header("📐 Tham số Phân Mảnh")
    fixed_size = st.slider("Fixed-size Chunk Size (từ/ký tự):", min_value=100, max_value=1000, value=350, step=50)
    fixed_overlap = st.slider("Fixed-size Overlap:", min_value=0, max_value=200, value=50, step=10)
    semantic_target = st.slider("Semantic Max Target (ký tự):", min_value=100, max_value=1000, value=400, step=50)
    
    st.divider()
    
    if st.button("🚀 Chạy lại Pipeline OCR & Chunking", use_container_width=True, type="primary"):
        with st.spinner("Đang chạy lại luồng chunking..."):
            raw_text = load_raw_text()
            if not raw_text:
                st.error("Không tìm thấy raw_text.txt. Vui lòng chạy python src/ocr_chunking.py lần đầu!")
            else:
                # Chạy lại chunking
                f_chunks = ocr_chunking.chunk_fixed_size(raw_text, chunk_size=fixed_size, overlap=fixed_overlap)
                s_chunks = ocr_chunking.chunk_semantic(raw_text)
                h_chunks = ocr_chunking.chunk_hierarchical(raw_text)
                
                # Cập nhật kết quả
                save_json(f_chunks, "chunks_fixed.json")
                save_json(s_chunks, "chunks_semantic.json")
                save_json(h_chunks, "chunks_hierarchical.json")
                st.success("Hoàn tất phân mảnh!")
                st.experimental_rerun() # Refresh app
    
    st.divider()
    st.markdown("**📂 Đã lưu trữ độc lập trong output/:**")
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    if os.path.exists(out_dir):
        files = os.listdir(out_dir)
        for f in files:
            st.caption(f"• `{f}`")

# -----------------
# MAIN CONTENT
# -----------------
st.markdown("""
<div class="main-header">
    <h1>🔍 RAG Foundation — Buổi 05: Trực Quan Hóa OCR & 3 Chiến Lược Chunking</h1>
    <p style="margin-top: 10px; opacity: 0.9;">Phân tích chi tiết quy trình chuyển đổi: PDF → Trích xuất Text / OCR Fallback → Chuẩn hóa Unicode NFC → Phân mảnh (Fixed-size, Semantic, Hierarchical)</p>
</div>
""", unsafe_allow_html=True)

# Load data
fixed_chunks = load_json("chunks_fixed.json")
semantic_chunks = load_json("chunks_semantic.json")
hierarchical_chunks = load_json("chunks_hierarchical.json")
raw_text = load_raw_text()

# Khởi tạo Tabs
t1, t2, t3, t4, t5 = st.tabs([
    "📊 1. Thống Kê & So Sánh", 
    "📄 2. Text Layer vs OCR", 
    "🧩 3. Trực Quan Hóa Chunks", 
    "🌳 4. Cây Phân Cấp Hierarchical", 
    "⚙️ 5. Đặc Tả SPEC & Môi Trường"
])

# -----------------
# TAB 1: THỐNG KÊ & SO SÁNH
# -----------------
with t1:
    st.header("📈 Bảng Thống Kê So Sánh 3 Chiến Lược Chunking")
    
    stat_fixed = calculate_stats(fixed_chunks)
    stat_sem = calculate_stats(semantic_chunks)
    stat_hier = calculate_stats(hierarchical_chunks)
    
    # Metrcis
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng Số File Raw", 1)
    c2.metric("Chunks Fixed-size", stat_fixed["count"])
    c3.metric("Chunks Semantic", stat_sem["count"])
    c4.metric("Chunks Hierarchical", stat_hier["count"])
    
    st.markdown("---")
    
    # Dataframe So sánh
    df = pd.DataFrame({
        "Chiến Lược": [
            "1. Fixed-size (Cố định + Overlap)", 
            "2. Semantic (Ngữ nghĩa tự nhiên)", 
            "3. Hierarchical (Cấu trúc phân cấp)"
        ],
        "Số Lượng Chunks": [stat_fixed["count"], stat_sem["count"], stat_hier["count"]],
        "Độ Dài Min (ký tự)": [stat_fixed["min"], stat_sem["min"], stat_hier["min"]],
        "Độ Dài Max (ký tự)": [stat_fixed["max"], stat_sem["max"], stat_hier["max"]],
        "Trung Bình (ký tự)": [stat_fixed["avg"], stat_sem["avg"], stat_hier["avg"]],
        "Đặc Điểm Chính": [
            "Cắt đều nhau theo kích thước, bảo toàn ngữ cảnh qua vùng gối đầu (overlap).",
            "Ưu tiên ngắt đoạn văn và dấu câu, giữ trọn vẹn câu văn có nghĩa.",
            "Phân cấp theo Chương -> Mục -> Điều/Khoản kèm breadcrumb metadata."
        ]
    })
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("📊 So Sánh Độ Dài Trung Bình & Phân Bố Chunk")
    
    # Bar Chart sử dụng Altair
    chart_data = pd.DataFrame({
        "Chiến Lược": ["Fixed-size", "Semantic", "Hierarchical"],
        "Độ Dài Trung Bình": [stat_fixed["avg"], stat_sem["avg"], stat_hier["avg"]]
    })
    
    bars = alt.Chart(chart_data).mark_bar(color='#3B82F6').encode(
        x=alt.X('Chiến Lược:N', axis=alt.Axis(labelAngle=0)),
        y='Độ Dài Trung Bình:Q',
        tooltip=['Chiến Lược', 'Độ Dài Trung Bình']
    ).properties(height=350)
    
    st.altair_chart(bars, use_container_width=True)

# -----------------
# TAB 2: TEXT LAYER VS OCR
# -----------------
with t2:
    st.header("📄 Kết quả trích xuất văn bản (Raw Text)")
    st.info("Quá trình kết hợp PyMuPDF (đọc text layer) và LlamaParse (OCR fallback) đã xuất ra văn bản chuẩn hóa Unicode NFC.")
    if raw_text:
        st.text_area("Nội dung thô (Raw Text)", raw_text, height=500)
    else:
        st.warning("Chưa có raw text. Hãy đảm bảo bạn đã chạy pipeline.")

# -----------------
# TAB 3: TRỰC QUAN HÓA CHUNKS
# -----------------
with t3:
    st.header("🧩 Khám phá chi tiết các Chunks")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        strategy_select = st.radio("Chọn chiến lược:", ["Fixed-size", "Semantic", "Hierarchical"])
    
    active_chunks = []
    if strategy_select == "Fixed-size":
        active_chunks = fixed_chunks
    elif strategy_select == "Semantic":
        active_chunks = semantic_chunks
    else:
        active_chunks = hierarchical_chunks
        
    with col2:
        if active_chunks:
            chunk_options = {c["chunk_id"]: c for c in active_chunks}
            selected_id = st.selectbox(f"Chọn Chunk ({len(active_chunks)} available):", options=list(chunk_options.keys()))
            
            if selected_id:
                sel = chunk_options[selected_id]
                st.markdown("**Nội dung (Text):**")
                st.success(sel.get("text", ""))
                
                st.markdown("**Metadata:**")
                st.json(sel.get("metadata", {}))
        else:
            st.warning("Không có dữ liệu chunks cho chiến lược này.")

# -----------------
# TAB 4: CÂY PHÂN CẤP HIERARCHICAL
# -----------------
with t4:
    st.header("🌳 Mô Phỏng Cây Phân Cấp (Hierarchical)")
    st.markdown("Chiến lược Hierarchical tách văn bản pháp lý thành các đơn vị tự nhiên. Dưới đây là danh sách các Điều đã được nhận diện:")
    
    if hierarchical_chunks:
        # Nhóm theo Điều (Legal Unit)
        for chunk in hierarchical_chunks:
            legal_unit = chunk.get("metadata", {}).get("legal_unit", "Không rõ")
            with st.expander(f"📖 {legal_unit} ({chunk.get('chunk_id')})"):
                st.write(chunk.get("text"))
    else:
        st.info("Chưa có chunk phân cấp. Vui lòng chạy chiến lược Hierarchical.")

# -----------------
# TAB 5: ĐẶC TẢ SPEC
# -----------------
with t5:
    st.header("⚙️ Đặc Tả Kỹ Thuật (SPEC) & Môi Trường")
    spec_content = load_spec()
    st.markdown(spec_content)
