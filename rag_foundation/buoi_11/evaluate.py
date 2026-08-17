import os
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from graph_retriever import get_context
from qa_chain import answer_question

# 5 câu hỏi kiểm thử từ đề bài
QUESTIONS = [
    "Nghị định 46/2023/NĐ-CP thay thế cho nghị định nào, và nghị định bị thay thế đó có nội dung gì nổi bật về kinh doanh bảo hiểm?",
    "Văn bản hợp nhất số 52/VBHN-NHNN được hợp nhất từ văn bản nào, và quy định về hồ sơ, thủ tục cấp giấy phép lần đầu của ngân hàng thương mại gồm những tài liệu gì?",
    "Thông tư số 01/2025/TT-NHNN quy định về cấp giấy phép quỹ tín dụng nhân dân được sửa đổi, bổ sung bởi văn bản nào, và những nội dung sửa đổi bổ sung chính là gì?",
    "Thông tư số 41/2016/TT-NHNN về tỷ lệ an toàn vốn của ngân hàng căn cứ vào luật nào, và luật đó quy định chức năng nhiệm vụ của cơ quan nào?",
    "Hoạt động giao nhận, vận chuyển tiền mặt và tài sản quý của Ngân hàng Nhà nước được điều chỉnh bởi Thông tư nào, và Thông tư đó có được sửa đổi bổ sung bởi văn bản nào không?"
]

def run_evaluation():
    output_file = os.path.join(os.path.dirname(__file__), "qa_comparison.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Đánh giá So sánh Multi-hop Graph RAG\n\n")
        
        for i, query in enumerate(QUESTIONS, 1):
            f.write(f"## Câu hỏi {i}: {query}\n\n")
            
            for hops in [0, 1, 2]:
                print(f"Đang xử lý Câu {i} với Hops = {hops}...")
                
                # Retrieve context
                context = get_context(query, k=5, hops=hops)
                
                # Get Answer
                answer = answer_question(query, context)
                
                f.write(f"### Với số bước nhảy (Hops) = {hops}\n")
                f.write(f"**Câu trả lời:**\n{answer}\n\n")
                
            f.write("---\n\n")
            
    print(f"Đã hoàn thành đánh giá. Báo cáo được lưu tại: {output_file}")

if __name__ == "__main__":
    run_evaluation()
