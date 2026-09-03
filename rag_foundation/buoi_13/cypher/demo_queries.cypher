// demo_queries.cypher

// A. Xem toàn bộ graph.
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m;

// B. Tìm kiểm soát giảm thiểu một rủi ro (Ví dụ: RR-001)
MATCH (k:KiemSoat)-[r:MITIGATES]->(rr:RuiRo {id: 'RR-001'})
RETURN k, r, rr;

// C. Tìm sự kiện của một rủi ro (Ví dụ: RR-001)
MATCH (rr:RuiRo {id: 'RR-001'})-[r:OBSERVED_AS]->(sk:SuKienRuiRo)
RETURN rr, r, sk;

// D. Tìm đường: KiemSoat -> RuiRo -> SuKienRuiRo
MATCH path = (k:KiemSoat)-[:MITIGATES]->(rr:RuiRo)-[:OBSERVED_AS]->(sk:SuKienRuiRo)
RETURN path;

// E. Tìm rủi ro không có kiểm soát
MATCH (rr:RuiRo)
WHERE NOT (:KiemSoat)-[:MITIGATES]->(rr)
RETURN rr;

// F. Tìm relation chưa VERIFIED (giả sử state = 'PROPOSED')
MATCH (a)-[r]->(b)
WHERE r.verification_status = 'PROPOSED'
RETURN a, r, b;
