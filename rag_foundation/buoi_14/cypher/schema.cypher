// Tạo constraint cho các node
CREATE CONSTRAINT vanban_id IF NOT EXISTS FOR (v:VanBan) REQUIRE v.id IS UNIQUE;
CREATE CONSTRAINT dieukhoan_id IF NOT EXISTS FOR (d:DieuKhoan) REQUIRE d.id IS UNIQUE;

// Xóa dữ liệu cũ của lab_session này nếu chạy lại
MATCH (n) WHERE n.lab_session = 'buoi_14' DETACH DELETE n;
