"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Tương tác trực tiếp với Cơ sở dữ liệu SQLite (ecommerce.db) 11 bảng cho cả Khách hàng và Admin.
"""

import os
import sys
import sqlite3
import random
from datetime import datetime

# Đảm bảo import db.py hoạt động từ mọi đường dẫn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_connection, init_db

# Khởi tạo CSDL SQLite
init_db()

def _verify_admin(conn, admin_id: int) -> bool:
    """Hàm bổ trợ kiểm tra xem user_id có vai trò ADMIN hay không."""
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE id = ?;", (int(admin_id),))
    r = cursor.fetchone()
    return r is not None and r["role"] == "ADMIN"


# --- GROUP 1: APIS ĐƠN HÀNG & SẢN PHẨM (CUSTOMER) ---

def create_order(user_id: int, product_id: int, quantity: int = 1, payment_method: str = "COD", shipping_address: str = "123 Nguyễn Huệ, Quận 1, TP.HCM") -> str:
    """Khách hàng: Khởi tạo đơn hàng mới và giả lập thanh toán trong CSDL SQLite."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Kiểm tra sản phẩm
        cursor.execute("SELECT id, name, price, stock, status FROM products WHERE id = ?;", (int(product_id),))
        p = cursor.fetchone()
        if not p:
            conn.close()
            return f"LỖI: Không tìm thấy sản phẩm ID #{product_id}."
            
        if p["stock"] < int(quantity):
            conn.close()
            return f"❌ ĐẶT HÀNG THẤT BẠI: Sản phẩm '{p['name']}' chỉ còn {p['stock']} cái trong kho (Yêu cầu: {quantity})."
            
        unit_price = p["price"]
        total_amount = unit_price * int(quantity) + 30000  # Phí ship 30,000 VNĐ
        order_code = f"ORD-{random.randint(1000, 9999)}"
        
        # 2. Thêm bản ghi đơn hàng orders
        cursor.execute("""
            INSERT INTO orders (user_id, order_code, total_amount, shipping_fee, status, payment_method, shipping_address)
            VALUES (?, ?, ?, 30000, 'CONFIRMED', ?, ?);
        """, (int(user_id), order_code, total_amount, payment_method.upper(), shipping_address))
        
        order_id = cursor.lastrowid
        
        # 3. Thêm chi tiết đơn order_items
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?);
        """, (order_id, int(product_id), int(quantity), unit_price))
        
        # 4. Trừ số lượng tồn kho product stock
        new_stock = p["stock"] - int(quantity)
        new_status = "ACTIVE" if new_stock > 0 else "OUT_OF_STOCK"
        cursor.execute("UPDATE products SET stock = ?, status = ? WHERE id = ?;", (new_stock, new_status, int(product_id)))
        
        # 5. Tạo vận chuyển shipping
        tracking_num = f"GHN{random.randint(100000, 999999)}"
        cursor.execute("""
            INSERT INTO shipping (order_id, carrier, tracking_number, status)
            VALUES (?, 'Giao Hàng Nhanh (GHN)', ?, 'CREATED');
        """, (order_id, tracking_num))
        
        conn.commit()
        conn.close()
        
        return (
            f"🎉 ĐẶT HÀNG THÀNH CÔNG!\n"
            f"- Mã đơn hàng: {order_code}\n"
            f"- Sản phẩm: {p['name']} (x{quantity})\n"
            f"- Tổng tiền (đã ship): {total_amount:,.0f} VNĐ\n"
            f"- Phương thức thanh toán: {payment_method.upper()} (Giả lập thành công)\n"
            f"- Trạng thái: CONFIRMED (Mã vận đơn: {tracking_num})."
        )
    except Exception as e:
        return f"LỖI THỰC THI ĐẶT HÀNG: {str(e)}"


def get_user_orders(user_id: int = 1, status_filter: str = "ALL") -> str:
    """Tra cứu danh sách đơn hàng của khách hàng theo user_id trong SQLite."""
    valid_statuses = ["ALL", "PENDING", "CONFIRMED", "PACKING", "SHIPPING", "DELIVERED", "CANCELLED"]
    status = str(status_filter).strip().upper()
    if status not in valid_statuses:
        return f"LỖI: status_filter '{status_filter}' không hợp lệ. Chọn: {', '.join(valid_statuses)}."

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                o.id,
                o.order_code,
                o.status,
                o.total_amount,
                o.payment_method,
                o.created_at,
                s.status AS shipping_status,
                s.tracking_number,
                (
                    SELECT GROUP_CONCAT(p.name || ' (x' || oi.quantity || ')', ', ')
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = o.id
                ) AS items,
                (
                    SELECT rr.return_code || ' - ' || rr.status
                    FROM return_requests rr
                    WHERE rr.order_id = o.id
                    ORDER BY rr.created_at DESC
                    LIMIT 1
                ) AS latest_return
            FROM orders o
            LEFT JOIN shipping s ON s.order_id = o.id
            WHERE o.user_id = ?
        """
        params = [int(user_id)]

        if status != "ALL":
            query += " AND o.status = ?"
            params.append(status)

        query += " ORDER BY o.created_at DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            suffix = "" if status == "ALL" else f" với trạng thái {status}"
            return f"Không tìm thấy đơn hàng nào cho User #{user_id}{suffix}."

        orders = []
        for r in rows:
            shipping = r["shipping_status"] or "CHƯA TẠO"
            tracking = f", vận đơn {r['tracking_number']}" if r["tracking_number"] else ""
            latest_return = f" | Đổi trả: {r['latest_return']}" if r["latest_return"] else ""
            orders.append(
                f"- {r['order_code']}: {r['status']} | Ship: {shipping}{tracking} | "
                f"Tổng: {r['total_amount']:,.0f} VNĐ | Thanh toán: {r['payment_method']} | "
                f"Ngày tạo: {r['created_at']} | Sản phẩm: {r['items'] or 'Chưa có sản phẩm'}{latest_return}"
            )

        return f"Danh sách đơn hàng của User #{user_id}:\n" + "\n".join(orders)
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_user_orders): {str(e)}"


def get_order_details(order_code: str) -> str:
    """Tra cứu chi tiết một đơn hàng trong CSDL SQLite."""
    code = order_code.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.order_code, o.user_id, o.status, o.total_amount, o.payment_method, o.shipping_address, o.created_at,
                   GROUP_CONCAT(p.name || ' (x' || oi.quantity || ')', ', ') AS items
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.order_code = ?
            GROUP BY o.id;
        """, (code,))
        
        r = cursor.fetchone()
        conn.close()
        
        if r:
            return (
                f"Thông tin đơn hàng {r['order_code']}:\n"
                f"- Khách hàng ID: {r['user_id']}\n"
                f"- Sản phẩm: {r['items']}\n"
                f"- Tổng tiền: {r['total_amount']:,} VNĐ (Thanh toán: {r['payment_method']})\n"
                f"- Địa chỉ giao: {r['shipping_address']}\n"
                f"- Trạng thái đơn: {r['status']}\n"
                f"- Ngày tạo đơn: {r['created_at']}"
            )
        return f"LỖI: Không tìm thấy mã đơn hàng '{order_code}' trong CSDL SQLite."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_order_details): {str(e)}"


def cancel_order(order_code: str, reason: str = "Đổi ý không mua nữa") -> str:
    """Hủy đơn hàng nếu đơn ở trạng thái PENDING hoặc CONFIRMED."""
    code = order_code.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM orders WHERE order_code = ?;", (code,))
        r = cursor.fetchone()
        
        if not r:
            conn.close()
            return f"LỖI: Không tìm thấy đơn hàng '{order_code}'."
            
        current_status = r["status"]
        if current_status in ["PENDING", "CONFIRMED"]:
            cursor.execute("UPDATE orders SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE order_code = ?;", (code,))
            conn.commit()
            conn.close()
            return f"✅ HỦY ĐƠN THÀNH CÔNG: Đơn hàng '{code}' đã chuyển sang trạng thái CANCELLED. Lý do: {reason}."
        
        conn.close()
        return f"❌ KHÔNG THỂ HỦY ĐƠN: Đơn hàng '{code}' hiện ở trạng thái {current_status}. Chỉ đơn PENDING hoặc CONFIRMED mới được phép hủy."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (cancel_order): {str(e)}"


def search_products(keyword: str) -> str:
    """Tra cứu thông tin sản phẩm trong CSDL SQLite."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, price, stock, status FROM products WHERE LOWER(name) LIKE ?;", (f"%{keyword.lower()}%",))
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            matches = [f"- [{r['id']}] {r['name']} | Giá: {r['price']:,} VNĐ | Tồn kho: {r['stock']} ({r['status']})" for r in rows]
            return "Kết quả tìm kiếm sản phẩm:\n" + "\n".join(matches)
        return f"Không tìm thấy sản phẩm nào khớp với từ khóa '{keyword}'."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (search_products): {str(e)}"


# --- GROUP 2: APIS VẬN CHUYỂN ---

def get_shipping_status(order_code: str) -> str:
    """Tra cứu thông tin vận chuyển của đơn hàng từ bảng shipping."""
    code = order_code.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.carrier, s.tracking_number, s.status, s.delivered_at
            FROM shipping s
            JOIN orders o ON s.order_id = o.id
            WHERE o.order_code = ?;
        """, (code,))
        
        ship = cursor.fetchone()
        conn.close()
        
        if ship:
            deliv = ship['delivered_at'] if ship['delivered_at'] else "Chưa giao hàng thành công"
            return (
                f"Thông tin vận chuyển đơn {code}:\n"
                f"- Đơn vị vận chuyển: {ship['carrier']}\n"
                f"- Mã vận đơn: {ship['tracking_number']}\n"
                f"- Trạng thái vận chuyển: {ship['status']}\n"
                f"- Ngày giao thực tế: {deliv}"
            )
        return f"LỖI: Không tìm thấy vận chuyển cho đơn hàng '{order_code}'."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_shipping_status): {str(e)}"


# --- GROUP 3: APIS ĐỔI TRẢ HÀNG (CUSTOMER) ---

def check_return_eligibility(order_code: str) -> str:
    """Kiểm tra điều kiện đổi trả của đơn hàng trong SQLite (Hạn 7 ngày kể từ ngày giao)."""
    code = order_code.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.status AS order_status, s.status AS shipping_status, s.delivered_at,
                   CAST((julianday('now') - julianday(s.delivered_at)) AS INTEGER) AS days_since_delivery
            FROM orders o
            LEFT JOIN shipping s ON o.id = s.order_id
            WHERE o.order_code = ?;
        """, (code,))
        
        r = cursor.fetchone()
        conn.close()
        
        if not r:
            return f"LỖI: Không tìm thấy đơn hàng '{order_code}' trong CSDL SQLite."
            
        if r["order_status"] != "DELIVERED" or r["shipping_status"] != "DELIVERED" or not r["delivered_at"]:
            return f"KHÔNG HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' chưa ở trạng thái giao thành công (Hiện tại: {r['order_status']})."
            
        days = r["days_since_delivery"]
        if days is not None and days <= 7:
            return f"HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao {days} ngày trước (Trong hạn bảo hành 7 ngày)."
        else:
            return f"KHÔNG HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao được {days} ngày (Quá hạn quy định 7 ngày)."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (check_return_eligibility): {str(e)}"


def create_return_request(order_code: str, reason: str = "DEFECTIVE", description: str = "Khách hàng đổi trả", image_url: str = "") -> str:
    """Khởi tạo đơn đổi trả trong bảng return_requests SQLite."""
    code = str(order_code).strip().upper()
    valid_reasons = ["DEFECTIVE", "WRONG_ITEM", "DAMAGED", "MIND_CHANGE"]
    reason_upper = str(reason).strip().upper()
    if reason_upper not in valid_reasons:
        return f"LỖI: Lý do đổi trả '{reason}' không hợp lệ. Chọn: {', '.join(valid_reasons)}."

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.id,
                o.user_id,
                o.status AS order_status,
                s.status AS shipping_status,
                s.delivered_at,
                CAST((julianday('now') - julianday(s.delivered_at)) AS INTEGER) AS days_since_delivery
            FROM orders o
            LEFT JOIN shipping s ON o.id = s.order_id
            WHERE o.order_code = ?;
        """, (code,))
        order_row = cursor.fetchone()

        if not order_row:
            conn.close()
            return f"TẠO ĐỔI TRẢ THẤT BẠI: Không tìm thấy đơn hàng '{code}'."

        if order_row["order_status"] != "DELIVERED" or order_row["shipping_status"] != "DELIVERED" or not order_row["delivered_at"]:
            conn.close()
            return f"TẠO ĐỔI TRẢ THẤT BẠI: Đơn '{code}' chưa giao thành công (đơn: {order_row['order_status']}, ship: {order_row['shipping_status'] or 'CHƯA TẠO'})."

        days = order_row["days_since_delivery"]
        if days is None or days > 7:
            conn.close()
            return f"TẠO ĐỔI TRẢ THẤT BẠI: Đơn '{code}' đã giao {days} ngày, quá hạn đổi trả 7 ngày."

        cursor.execute("""
            SELECT return_code, status
            FROM return_requests
            WHERE order_id = ?
              AND status IN ('REQUESTED', 'REVIEWING', 'APPROVED', 'RETURNING')
            ORDER BY created_at DESC
            LIMIT 1;
        """, (order_row["id"],))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return f"TẠO ĐỔI TRẢ THẤT BẠI: Đơn '{code}' đã có yêu cầu {existing['return_code']} đang ở trạng thái {existing['status']}."

        ret_code = f"RET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
        cursor.execute("""
            INSERT INTO return_requests (return_code, order_id, user_id, reason, description, status, image_url)
            VALUES (?, ?, ?, ?, ?, 'REQUESTED', ?);
        """, (ret_code, order_row["id"], order_row["user_id"], reason_upper, description, image_url))

        conn.commit()
        conn.close()

        return (
            f"✅ TẠO YÊU CẦU ĐỔI TRẢ THÀNH CÔNG!\n"
            f"- Mã yêu cầu: {ret_code}\n"
            f"- Đơn hàng: {code}\n"
            f"- Điều kiện: Đã giao {days} ngày, còn trong hạn 7 ngày\n"
            f"- Lý do: {reason_upper}\n"
            f"- Mô tả: {description}\n"
            f"- Trạng thái: REQUESTED (chờ Admin duyệt)."
        )
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (create_return_request): {str(e)}"


def get_return_request_status(order_code: str) -> str:
    """Tra cứu tiến độ đơn đổi trả trong SQLite."""
    code = order_code.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.return_code, o.order_code, r.reason, r.description, r.status, r.created_at
            FROM return_requests r
            JOIN orders o ON r.order_id = o.id
            WHERE o.order_code = ? OR r.return_code = ?;
        """, (code, code))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            matches = [f"- Mã đổi trả: {r['return_code']} | Đơn: {r['order_code']} | Trạng thái: {r['status']} | Lý do: {r['reason']} ({r['description']})" for r in rows]
            return "Thông tin yêu cầu đổi trả (SQLite):\n" + "\n".join(matches)
        return f"Chưa tìm thấy yêu cầu đổi trả nào cho đơn hàng '{order_code}'."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_return_request_status): {str(e)}"


def cancel_return_request(return_id: str) -> str:
    """Hủy đơn đổi trả nếu ở trạng thái REQUESTED."""
    rid = return_id.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM return_requests WHERE return_code = ?;", (rid,))
        r = cursor.fetchone()
        
        if not r:
            conn.close()
            return f"LỖI: Không tìm thấy mã yêu cầu đổi trả '{return_id}'."
            
        if r["status"] == "REQUESTED":
            cursor.execute("UPDATE return_requests SET status = 'CANCELLED', updated_at = CURRENT_TIMESTAMP WHERE return_code = ?;", (rid,))
            conn.commit()
            conn.close()
            return f"✅ ĐÃ HỦY: Yêu cầu đổi trả '{rid}' đã được hủy thành công."
        
        conn.close()
        return f"❌ KHÔNG THỂ HỦY: Yêu cầu đổi trả '{rid}' đang ở trạng thái {r['status']}."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (cancel_return_request): {str(e)}"


def get_user_profile(user_id: int = 1) -> str:
    """Tra cứu thông tin tài khoản người dùng từ bảng users SQLite."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, full_name, email, phone, role, created_at FROM users WHERE id = ?;", (int(user_id),))
        u = cursor.fetchone()
        conn.close()
        
        if u:
            return f"Thông tin tài khoản User #{u['id']}: Họ tên: {u['full_name']} | Email: {u['email']} | SĐT: {u['phone']} | Vai trò: {u['role']}"
        return f"LỖI: Không tìm thấy thông tin tài khoản cho User #{user_id}."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_user_profile): {str(e)}"


# --- GROUP 5: APIS QUẢN TRỊ VIÊN (ADMIN TOOLS) ---

def add_product(admin_id: int, name: str, category_id: int, price: float, stock: int, description: str = "Sản phẩm mới") -> str:
    """Admin: Thêm sản phẩm mới vào danh mục sản phẩm trong SQLite."""
    try:
        conn = get_connection()
        if not _verify_admin(conn, admin_id):
            conn.close()
            return f"🚫 TỪ CHỐI QUYỀN: User #{admin_id} không có quyền ADMIN để thêm sản phẩm."
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (category_id, name, description, price, stock, status)
            VALUES (?, ?, ?, ?, ?, 'ACTIVE');
        """, (int(category_id), name, description, float(price), int(stock)))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return f"✅ THÊM SẢN PHẨM THÀNH CÔNG (ADMIN)! Mã sản phẩm #{new_id} - '{name}' | Giá: {float(price):,} VNĐ | Tồn kho: {stock} cái."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (add_product): {str(e)}"


def update_product_stock(admin_id: int, product_id: int, new_stock: int) -> str:
    """Admin: Cập nhật số lượng tồn kho sản phẩm trong CSDL SQLite."""
    try:
        conn = get_connection()
        if not _verify_admin(conn, admin_id):
            conn.close()
            return f"🚫 TỪ CHỐI QUYỀN: User #{admin_id} không có quyền ADMIN."
            
        cursor = conn.cursor()
        status_val = "ACTIVE" if int(new_stock) > 0 else "OUT_OF_STOCK"
        
        cursor.execute("UPDATE products SET stock = ?, status = ? WHERE id = ?;", (int(new_stock), status_val, int(product_id)))
        if cursor.rowcount == 0:
            conn.close()
            return f"LỖI: Không tìm thấy sản phẩm #{product_id}."
            
        conn.commit()
        conn.close()
        return f"✅ CẬP NHẬT KHO THÀNH CÔNG (ADMIN)! Sản phẩm #{product_id} -> Số lượng tồn kho mới: {new_stock} (Trạng thái: {status_val})."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (update_product_stock): {str(e)}"


def update_order_status(admin_id: int, order_code: str, new_status: str) -> str:
    """Admin: Cập nhật trạng thái đơn hàng trong SQLite (PENDING, CONFIRMED, PACKING, SHIPPING, DELIVERED, CANCELLED)."""
    code = order_code.strip().upper()
    valid_statuses = ['PENDING', 'CONFIRMED', 'PACKING', 'SHIPPING', 'DELIVERED', 'CANCELLED']
    status_upper = new_status.strip().upper()
    
    if status_upper not in valid_statuses:
        return f"LỖI: Trạng thái '{new_status}' không hợp lệ. Trạng thái hợp lệ: {', '.join(valid_statuses)}."
        
    try:
        conn = get_connection()
        if not _verify_admin(conn, admin_id):
            conn.close()
            return f"🚫 TỪ CHỐI QUYỀN: User #{admin_id} không có quyền ADMIN."
            
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_code = ?;", (status_upper, code))
        if cursor.rowcount == 0:
            conn.close()
            return f"LỖI: Không tìm thấy đơn hàng '{code}'."
            
        conn.commit()
        conn.close()
        return f"✅ CẬP NHẬT ĐƠN HÀNG THÀNH CÔNG (ADMIN)! Đơn hàng '{code}' đã đổi trạng thái sang '{status_upper}'."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (update_order_status): {str(e)}"


def review_return_request(admin_id: int, return_code: str, action: str, note: str = "Đã xem xét") -> str:
    """Admin: Duyệt (APPROVED) hoặc Từ chối (REJECTED) đơn đổi trả từ khách hàng."""
    rcode = return_code.strip().upper()
    act = action.strip().upper()
    
    target_status = "APPROVED" if act in ["APPROVE", "APPROVED"] else "REJECTED" if act in ["REJECT", "REJECTED"] else None
    if not target_status:
        return f"LỖI: Hành động '{action}' không hợp lệ. Chỉ chấp nhận 'APPROVE' hoặc 'REJECT'."
        
    try:
        conn = get_connection()
        if not _verify_admin(conn, admin_id):
            conn.close()
            return f"🚫 TỪ CHỐI QUYỀN: User #{admin_id} không có quyền ADMIN."
            
        cursor = conn.cursor()
        cursor.execute("UPDATE return_requests SET status = ?, description = description || ' | Admin Note: ' || ?, updated_at = CURRENT_TIMESTAMP WHERE return_code = ?;", (target_status, note, rcode))
        if cursor.rowcount == 0:
            conn.close()
            return f"LỖI: Không tìm thấy mã yêu cầu đổi trả '{rcode}'."
            
        conn.commit()
        conn.close()
        return f"✅ DUYỆT ĐỔI TRẢ THÀNH CÔNG (ADMIN)! Yêu cầu '{rcode}' đã chuyển sang trạng thái '{target_status}'. Ghi chú: {note}."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (review_return_request): {str(e)}"


def get_admin_dashboard_summary(admin_id: int = 3) -> str:
    """Admin: Xem báo cáo thống kê tổng quan (Đơn hàng, Đổi trả chờ duyệt, Sản phẩm, Doanh thu)."""
    try:
        conn = get_connection()
        if not _verify_admin(conn, admin_id):
            conn.close()
            return f"🚫 TỪ CHỐI QUYỀN: User #{admin_id} không có quyền ADMIN."
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders;")
        total_orders = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM return_requests WHERE status = 'REQUESTED';")
        pending_returns = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products;")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'CANCELLED';")
        revenue = cursor.fetchone()[0]
        
        conn.close()
        return (
            f"📊 BÁO CÁO ADMIN DASHBOARD SUMMARY (SQLITE):\n"
            f"- Tổng số đơn hàng: {total_orders}\n"
            f"- Đơn đổi trả chờ duyệt (REQUESTED): {pending_returns}\n"
            f"- Tổng số sản phẩm trong hệ thống: {total_products}\n"
            f"- Tổng doanh thu (các đơn active): {revenue:,.0f} VNĐ"
        )
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_admin_dashboard_summary): {str(e)}"


# Registry 16 Tools cho ReAct Agent
AVAILABLE_TOOLS = {
    # Customer Tools
    "create_order": create_order,
    "get_user_orders": get_user_orders,
    "get_order_details": get_order_details,
    "cancel_order": cancel_order,
    "search_products": search_products,
    "get_shipping_status": get_shipping_status,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
    "get_return_request_status": get_return_request_status,
    "cancel_return_request": cancel_return_request,
    "get_user_profile": get_user_profile,
    
    # Admin Tools
    "add_product": add_product,
    "update_product_stock": update_product_stock,
    "update_order_status": update_order_status,
    "review_return_request": review_return_request,
    "get_admin_dashboard_summary": get_admin_dashboard_summary,
}
