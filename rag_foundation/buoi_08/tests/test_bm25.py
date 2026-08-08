import unittest
from advanced_rag import tokenize_vi_legal, bm25_search

class TestBM25(unittest.TestCase):
    def test_tokenizer_vietnamese(self):
        # 1. Tokenizer giữ dấu tiếng Việt.
        text = "Cơ cấu lại thời hạn trả nợ"
        tokens = tokenize_vi_legal(text)
        self.assertEqual(tokens, ["cơ", "cấu", "lại", "thời", "hạn", "trả", "nợ"])

    def test_tokenizer_numbers_and_legal_terms(self):
        # 2. Tokenizer giữ số Điều/Khoản.
        text = "Điều 7, Khoản 2"
        tokens = tokenize_vi_legal(text)
        self.assertEqual(tokens, ["điều", "7", "khoản", "2"])

    def test_exact_legal_term_ranking(self):
        # 4. Exact legal term được xếp trên đoạn không chứa từ khóa.
        chunks = [
            {"chunk_id": "c1", "text": "Đoạn này không chứa từ khóa", "source": "A", "page_start": 1, "page_end": 1},
            {"chunk_id": "c2", "text": "Khoản 2 Điều 7 Cơ cấu lại thời hạn", "source": "A", "page_start": 2, "page_end": 2},
            {"chunk_id": "c3", "text": "Một văn bản khác nói về thời hạn", "source": "A", "page_start": 3, "page_end": 3}
        ]
        res = bm25_search("Điều 7", chunks, candidate_k=5)
        self.assertEqual(res[0]["chunk_id"], "c2")

    def test_candidate_k_larger_than_corpus(self):
        # 5. candidate_k lớn hơn corpus vẫn chạy.
        chunks = [{"chunk_id": "c1", "text": "hello", "source": "A", "page_start": 1, "page_end": 1}]
        res = bm25_search("hello", chunks, candidate_k=100)
        self.assertEqual(len(res), 1)

    def test_empty_question_fails(self):
        # 6. Empty question fail.
        with self.assertRaises(ValueError):
            bm25_search("", [{"chunk_id": "c1", "text": "a", "source": "A", "page_start": 1, "page_end": 1}], 5)
        
        with self.assertRaises(ValueError):
            bm25_search("   ", [{"chunk_id": "c1", "text": "a", "source": "A", "page_start": 1, "page_end": 1}], 5)

    def test_tie_break_deterministic(self):
        # 7. Tie-break deterministic theo chunk_id
        # c2 và c1 giống hệt nhau về nội dung
        chunks = [
            {"chunk_id": "c2", "text": "chung nội dung", "source": "A", "page_start": 1, "page_end": 1},
            {"chunk_id": "c1", "text": "chung nội dung", "source": "A", "page_start": 2, "page_end": 2}
        ]
        res = bm25_search("chung", chunks, candidate_k=5)
        # Score sẽ bằng nhau, nhưng c1 xếp trước c2 do sort chunk_id (chuỗi "c1" < "c2")
        self.assertEqual(res[0]["chunk_id"], "c1")
        self.assertEqual(res[1]["chunk_id"], "c2")

if __name__ == '__main__':
    unittest.main()
