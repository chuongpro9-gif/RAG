import unittest
from unittest.mock import patch, MagicMock
from advanced_rag import query_advanced

class TestPipeline(unittest.TestCase):
    @patch("advanced_rag.bm25_search")
    @patch("advanced_rag.semantic_search")
    @patch("advanced_rag.rerank_candidates")
    @patch("rag.load_chunks")
    def test_query_skip_generation(self, mock_load, mock_rerank, mock_sem, mock_bm25):
        # 13. Pipeline mode check.
        mock_load.return_value = [{"chunk_id": "c1", "strategy": "hierarchical", "text": "t"}]
        mock_bm25.return_value = [{"chunk_id": "c1", "bm25_rank": 1, "text": "t"}]
        
        # Test bm25
        ans, chunks, trace = query_advanced("Q", "hierarchical", "bm25", skip_generation=True)
        self.assertEqual(ans, "")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "c1")
        
        # Test unknown mode
        with self.assertRaises(ValueError):
            query_advanced("Q", "hierarchical", "unknown_mode")

if __name__ == '__main__':
    unittest.main()
