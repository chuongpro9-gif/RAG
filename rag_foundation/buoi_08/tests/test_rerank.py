import unittest
from advanced_rag import rerank_candidates

class TestReranker(unittest.TestCase):
    def test_reranker_sorting_and_movement(self):
        # Fake reranker: trả điểm tùy ý
        def fake_reranker(q, texts):
            return [1.0, -1.0, 5.0] # chunk1 được 1.0, chunk2 được -1.0, chunk3 được 5.0
            
        candidates = [
            {"chunk_id": "c1", "text": "doc1", "fused_rank": 1},
            {"chunk_id": "c2", "text": "doc2", "fused_rank": 2},
            {"chunk_id": "c3", "text": "doc3", "fused_rank": 3},
        ]
        
        final_res, _ = rerank_candidates("Q", candidates, fake_reranker=fake_reranker)
        
        # Sort desc theo score: c3(5.0), c1(1.0), c2(-1.0)
        self.assertEqual(final_res[0]["chunk_id"], "c3")
        self.assertEqual(final_res[1]["chunk_id"], "c1")
        self.assertEqual(final_res[2]["chunk_id"], "c2")
        
        self.assertEqual(final_res[0]["rank_change"], 3 - 1) # từ hạng 3 lên 1 (+2)
        self.assertEqual(final_res[1]["rank_change"], 1 - 2) # từ hạng 1 xuống 2 (-1)
        self.assertEqual(final_res[2]["rank_change"], 2 - 3) # từ hạng 2 xuống 3 (-1)
        
    def test_reranker_unavailable_no_fallback(self):
        with self.assertRaises(RuntimeError) as context:
            # Sẽ gọi thật, nhưng nếu không có package hoặc internet sẽ quăng lỗi RuntimeError
            # Nhưng do test chạy unit nên module transformer có thể k chạy nổi
            # Chúng ta sẽ mock để raise Exception
            def fail_func(*args):
                raise Exception("Network Error")
            rerank_candidates("Q", [{"chunk_id": "c1", "text": "d1", "fused_rank": 1}], fake_reranker=fail_func)
            
        self.assertTrue("reranker_unavailable" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
