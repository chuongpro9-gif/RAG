import unittest
from unittest.mock import patch, MagicMock
import tempfile
import pathlib
import json
import shutil
import os
import sys

# Đưa thư mục cha vào path để import
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
import rag

class TestRAGLoader(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch('rag.INPUT_CHUNKS_DIR', pathlib.Path(self.test_dir))
        self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def write_json(self, name, data):
        with open(os.path.join(self.test_dir, name), "w", encoding="utf-8") as f:
            json.dump(data, f)
            
    def test_load_list(self):
        # 1. Loader đọc JSON list
        self.write_json("test1.json", [{"chunk_id": "c1", "strategy": "hierarchical", "source": "A.pdf", "page_start": 1, "page_end": 1, "text": "Hello"}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "c1")
        
    def test_load_object_with_chunks(self):
        # 2. Loader đọc object có field chunks
        self.write_json("test2.json", {"chunks": [{"chunk_id": "c2", "strategy": "hierarchical", "source": "A.pdf", "page_start": 1, "page_end": 1, "text": "Hello"}]})
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(len(chunks), 1)
        
    def test_only_correct_strategy(self):
        # 3. Chỉ lấy đúng strategy
        self.write_json("test3.json", [
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "A.pdf", "page_start": 1, "page_end": 1, "text": "H"},
            {"chunk_id": "c2", "strategy": "semantic", "source": "A.pdf", "page_start": 1, "page_end": 1, "text": "S"}
        ])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["strategy"], "hierarchical")
        
    def test_missing_fields(self):
        # 4. Thiếu field bắt buộc phải fail
        self.write_json("test4.json", [{"chunk_id": "c1", "strategy": "hierarchical"}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(len(chunks), 0)
        self.assertIn("Thiếu trường bắt buộc", stats["errors"][0])
        
    def test_wrong_types(self):
        # 5. Field sai kiểu phải fail
        self.write_json("test5.json", [{"chunk_id": 123, "strategy": "hierarchical", "source": "A", "page_start": 1, "page_end": 1, "text": "A"}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertIn("chunk_id, strategy, source, text phải là string.", stats["errors"][0])

    def test_boolean_page(self):
        # 6. Boolean không được chấp nhận làm page number
        self.write_json("test6.json", [{"chunk_id": "c1", "strategy": "hierarchical", "source": "A", "page_start": True, "page_end": False, "text": "A"}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertIn("page_start và page_end phải là integer", stats["errors"][0])

    def test_invalid_page_range(self):
        # 7. page_start > page_end phải fail
        self.write_json("test7.json", [{"chunk_id": "c1", "strategy": "hierarchical", "source": "A", "page_start": 5, "page_end": 2, "text": "A"}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertIn("Page range không hợp lệ", stats["errors"][0])

    def test_empty_text(self):
        # 8. Text rỗng bị bỏ qua và thống kê đúng
        self.write_json("test8.json", [{"chunk_id": "c1", "strategy": "hierarchical", "source": "A", "page_start": 1, "page_end": 1, "text": "   "}])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(stats["empty_text_skipped"], 1)

    def test_duplicate_chunk_id(self):
        # 9. Duplicate chunk_id phải fail
        self.write_json("test9.json", [
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "A", "page_start": 1, "page_end": 1, "text": "A"},
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "A", "page_start": 1, "page_end": 1, "text": "B"}
        ])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertEqual(len(chunks), 1)
        self.assertIn("Duplicate chunk_id", stats["errors"][0])
        
    def test_record_not_dict(self):
        # 38. Loader chặn record không phải JSON object
        self.write_json("test38.json", ["Just a string"])
        chunks, stats = rag.load_chunks("hierarchical")
        self.assertIn("Record không phải là JSON object.", stats["errors"][0])

class TestRAGEmbeddingAndChroma(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patch_chroma = patch('rag.CHROMA_STORAGE', pathlib.Path(self.test_dir) / "chroma")
        self.patch_chroma.start()
        
        # Patch load_chunks
        self.patch_load = patch('rag.load_chunks', return_value=([
            {"chunk_id": "c1", "strategy": "hierarchical", "source": "A.pdf", "page_start": 1, "page_end": 1, "text": "Hello"}
        ], {}))
        self.patch_load.start()
        
    def tearDown(self):
        self.patch_chroma.stop()
        self.patch_load.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('rag.GEMINI_API_KEY', 'fake_key')
    @patch('rag.GEMINI_EMBEDDING_DIM', 128)
    def test_embedding_mock(self):
        with patch('rag.get_embedding', return_value=[0.1]*128):
            rag.index_data("hierarchical", reset=True)
            # 10. Index hai lần không tăng record count
            rag.index_data("hierarchical", reset=False)
            
            client = rag.get_chroma_client()
            col = client.get_collection(rag.get_collection_name("hierarchical"), embedding_function=None)
            self.assertEqual(col.count(), 1)
            
            # 11. Metadata citation được lưu đầy đủ
            metadata = col.get()["metadatas"][0]
            self.assertIn("source", metadata)
            self.assertIn("page_start", metadata)
            
    def test_no_api_key(self):
        # 20. Thiếu API key phải fail rõ
        with patch('rag.GEMINI_API_KEY', None):
            with self.assertRaises(RuntimeError):
                rag.index_data("hierarchical")
                
    def test_embedding_wrong_dim(self):
        # 17. Embedding trả sai dimension phải fail
        with patch('rag.GEMINI_API_KEY', 'fake_key'):
            with patch('rag.get_embedding', return_value=[0.1]*100):
                with self.assertRaises(RuntimeError):
                    rag.index_data("hierarchical")

    def test_collection_identity(self):
        # 12, 13. Collection identity
        with patch('rag.GEMINI_EMBEDDING_DIM', 128):
            n1 = rag.get_collection_name("hierarchical")
            n2 = rag.get_collection_name("semantic")
            self.assertNotEqual(n1, n2)
            
        with patch('rag.GEMINI_EMBEDDING_DIM', 768):
            n3 = rag.get_collection_name("hierarchical")
            self.assertNotEqual(n1, n3)

class TestRAGRetrieval(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patch_chroma = patch('rag.CHROMA_STORAGE', pathlib.Path(self.test_dir) / "chroma")
        self.patch_chroma.start()
        
    def tearDown(self):
        self.patch_chroma.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_empty_collection(self):
        # 26. Collection rỗng phải fail rõ.
        # Tạo thủ công 1 collection rỗng
        client = rag.get_chroma_client()
        col = client.get_or_create_collection(rag.get_collection_name("hierarchical"), embedding_function=None)
        
        with self.assertRaises(ValueError):
            rag.query_rag("Câu hỏi?", "hierarchical", 5)

    @patch('rag.GEMINI_EMBEDDING_DIM', 128)
    @patch('rag.GEMINI_API_KEY', 'fake')
    @patch('rag.get_embedding', return_value=[0.1]*128)
    def test_retrieval(self, mock_emb):
        client = rag.get_chroma_client()
        col = client.get_or_create_collection(rag.get_collection_name("hierarchical"), embedding_function=None, metadata={"strategy": "hierarchical", "embedding_dim": 128, "embedding_model": rag.GEMINI_EMBEDDING_MODEL})
        col.add(
            ids=["c1", "c2"],
            embeddings=[[0.1]*128, [0.9]*128],
            documents=["Doc1", "Doc2"],
            metadatas=[{"source": "A", "page_start":1, "page_end":1, "chunk_id": "c1"}, {"source": "B", "page_start":2, "page_end":3, "chunk_id": "c2"}]
        )
        
        with patch('rag.RAG_MAX_DISTANCE', 0.5):
            res = rag.query_rag("Q?", "hierarchical", 5)
            # 28, 36. Status insufficient generation due to mock genai fail -> retrieval_only
            self.assertEqual(res["status"], "retrieval_only")
                
            # Check citations / confidence gate
            evs = res["evidence"]
            self.assertEqual(len(evs), 2)
                # Tùy thuật toán distance, nhưng chroma trả về id
                
if __name__ == '__main__':
    unittest.main()
