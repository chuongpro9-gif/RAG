import unittest
from evaluate import calculate_recall_at_k, calculate_mrr_at_k, calculate_ndcg_at_k

class TestEvaluation(unittest.TestCase):
    def test_metrics(self):
        # 14. Recall, MRR, nDCG calculation correctness.
        relevant = ["c1", "c3"]
        retrieved = ["c2", "c1", "c4", "c3", "c5"] # c1 rank 2, c3 rank 4
        
        # k=2: ["c2", "c1"] -> c1 relevant
        self.assertEqual(calculate_recall_at_k(retrieved, relevant, 2), 0.5) # 1/2
        self.assertEqual(calculate_mrr_at_k(retrieved, relevant, 2), 0.5) # 1/2
        
        # k=4: ["c2", "c1", "c4", "c3"] -> c1, c3 relevant
        self.assertEqual(calculate_recall_at_k(retrieved, relevant, 4), 1.0)
        self.assertEqual(calculate_mrr_at_k(retrieved, relevant, 4), 0.5) # c1 at rank 2
        
        # NDCG@4
        import math
        # DCG = rel_c1 / log2(2+1) + rel_c3 / log2(4+1) = 1/log2(3) + 1/log2(5) = 1/1.585 + 1/2.321 = 0.63 + 0.43 = 1.06
        # IDCG = 1/log2(2) + 1/log2(3) = 1 + 0.63 = 1.63
        dcg = 1/math.log2(3) + 1/math.log2(5)
        idcg = 1/math.log2(2) + 1/math.log2(3)
        self.assertAlmostEqual(calculate_ndcg_at_k(retrieved, relevant, 4), dcg/idcg, places=4)

if __name__ == '__main__':
    unittest.main()
