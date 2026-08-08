import unittest
from unittest.mock import patch, MagicMock
from advanced_rag import semantic_search

class TestSemanticSearch(unittest.TestCase):
    @patch("advanced_rag.get_config", side_effect=lambda k, d, t=str: d if k != "GEMINI_EMBEDDING_DIM" else 128)
    @patch("rag.get_embedding", return_value=[0.1] * 128)
    @patch("rag.get_chroma_client")
    def test_semantic_search_success(self, mock_client, mock_emb, mock_cfg):
        mock_col = MagicMock()
        mock_col.metadata = {"strategy": "hierarchical", "embedding_dim": 128}
        mock_col.count.return_value = 2
        mock_col.query.return_value = {
            "ids": [["c1", "c2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"source": "A", "page_start": 1, "page_end": 1}, {"source": "B", "page_start": 2, "page_end": 2}]]
        }
        
        # Setup mock client to return mock collection
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_col
        mock_client.return_value = mock_client_instance
        
        res = semantic_search("Câu hỏi?", 5, "hierarchical")
        
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["chunk_id"], "c1")
        self.assertEqual(res[0]["semantic_rank"], 1)
        self.assertEqual(res[1]["chunk_id"], "c2")

    @patch("rag.get_chroma_client")
    def test_semantic_search_mismatch(self, mock_client):
        mock_col = MagicMock()
        # metadata sai dim (ví dụ thực tế là 768 nhưng config là 128)
        mock_col.metadata = {"strategy": "hierarchical", "embedding_dim": 999}
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.return_value = mock_col
        mock_client.return_value = mock_client_instance
        
        with self.assertRaises(ValueError) as context:
            semantic_search("Câu hỏi?", 5, "hierarchical")
            
        self.assertTrue("mismatch" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
