import unittest
from unittest.mock import patch
from advanced_rag import hybrid_search

class TestHybridRRF(unittest.TestCase):
    @patch("advanced_rag.bm25_search")
    @patch("advanced_rag.semantic_search")
    @patch("advanced_rag.RRF_K", 60)
    @patch("advanced_rag.RRF_BM25_WEIGHT", 1.0)
    @patch("advanced_rag.RRF_SEMANTIC_WEIGHT", 1.0)
    def test_rrf_formula_and_overlap(self, mock_sem, mock_bm25):
        # 9. Formula và weights.
        # 10. Union/overlap/de-duplicate.
        # 11. Missing branch contribution.
        mock_bm25.return_value = [
            {"chunk_id": "c1", "text": "text1", "source": "A", "page_start": 1, "page_end": 1, "bm25_rank": 1, "bm25_score": 5.0},
            {"chunk_id": "c2", "text": "text2", "source": "A", "page_start": 2, "page_end": 2, "bm25_rank": 2, "bm25_score": 4.0},
        ]
        mock_sem.return_value = [
            {"chunk_id": "c2", "text": "text2", "source": "A", "page_start": 2, "page_end": 2, "semantic_rank": 1, "semantic_distance": 0.1},
            {"chunk_id": "c3", "text": "text3", "source": "A", "page_start": 3, "page_end": 3, "semantic_rank": 2, "semantic_distance": 0.2},
        ]
        
        res, trace = hybrid_search("Q", "hierarchical", [])
        
        self.assertEqual(len(res), 3)
        self.assertEqual(trace["union_count"], 3)
        self.assertEqual(trace["overlap_count"], 1) # c2
        
        # Tính điểm rrf:
        # c1: 1/(60+1) = 0.01639
        # c2: 1/(60+2) + 1/(60+1) = 0.016129 + 0.016393 = 0.03252
        # c3: 1/(60+2) = 0.016129
        # Vậy rank sẽ là: c2 (0.03252) -> c1 (0.01639) -> c3 (0.01612)
        self.assertEqual(res[0]["chunk_id"], "c2")
        self.assertEqual(res[1]["chunk_id"], "c1")
        self.assertEqual(res[2]["chunk_id"], "c3")
        
        self.assertEqual(res[0]["matched_by"], ["bm25", "semantic"])
        self.assertEqual(res[1]["matched_by"], ["bm25"])
        self.assertEqual(res[2]["matched_by"], ["semantic"])

    @patch("advanced_rag.bm25_search")
    @patch("advanced_rag.semantic_search")
    def test_metadata_mismatch(self, mock_sem, mock_bm25):
        # 12. Metadata mismatch.
        mock_bm25.return_value = [
            {"chunk_id": "c1", "text": "text1", "source": "A", "page_start": 1, "page_end": 1, "bm25_rank": 1, "bm25_score": 5.0},
        ]
        mock_sem.return_value = [
            {"chunk_id": "c1", "text": "text_different", "source": "A", "page_start": 1, "page_end": 1, "semantic_rank": 1, "semantic_distance": 0.1},
        ]
        
        with self.assertRaises(ValueError) as context:
            hybrid_search("Q", "hierarchical", [])
        self.assertTrue("Metadata mismatch" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
