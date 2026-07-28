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
    """
Create a new order and simulate payment in the SQLite database.

Business Flow:
    - Validate product exists.
    - Validate inventory.
    - Create order.
    - Create order items.
    - Update product stock.
    - Create shipping record.

Args:
    user_id (int):
        Customer ID.

    product_id (int):
        Product ID.

    quantity (int, optional):
        Quantity to purchase.
        Default = 1.

    payment_method (str, optional):
        Payment method.
        Example:
            "COD"
            "BANK"

    shipping_address (str, optional):
        Delivery address.

Returns:
    str:
        Success:
            Human-readable order confirmation.

        Failure:
            Product not found.
            Out of stock.
            SQLite execution error.

Database:
    - products
    - orders
    - order_items
    - shipping

Error Contract:
    Never raises exceptions.
    Always returns a readable string.
"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
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
        
        cursor.execute("""
            INSERT INTO orders (user_id, order_code, total_amount, shipping_fee, status, payment_method, shipping_address)
            VALUES (?, ?, ?, 30000, 'DELIVERED', ?, ?);
        """, (int(user_id), order_code, total_amount, payment_method.upper(), shipping_address))
        
        order_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?);
        """, (order_id, int(product_id), int(quantity), unit_price))
        
        new_stock = p["stock"] - int(quantity)
        new_status = "ACTIVE" if new_stock > 0 else "OUT_OF_STOCK"
        cursor.execute("UPDATE products SET stock = ?, status = ? WHERE id = ?;", (new_stock, new_status, int(product_id)))
        
        tracking_num = f"GHN{random.randint(100000, 999999)}"
        cursor.execute("""
            INSERT INTO shipping (order_id, carrier, tracking_number, status, delivered_at)
            VALUES (?, 'Giao Hàng Nhanh (GHN)', ?, 'DELIVERED', CURRENT_TIMESTAMP);
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
    """
Retrieve all orders of a customer.

Args:
    user_id (int):
        Customer ID.

    status_filter (str, optional):
        Filter by order status.
        Default = "ALL".

Returns:
    str:
        List of matching orders or readable error.

Database:
    - orders
    - order_items
    - products

Error Contract:
    Never raises exceptions.
"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT o.order_code, o.status, o.total_amount, GROUP_CONCAT(p.name || ' (x' || oi.quantity || ')', ', ') AS items
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = ?
        """
        params = [int(user_id)]
        
        if status_filter.upper() != "ALL":
            query += " AND o.status = ?"
            params.append(status_filter.upper())
            
        query += " GROUP BY o.id ORDER BY o.created_at DESC;"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            orders = [f"- {r['order_code']}: Trạng thái {r['status']} | Giá trị: {r['total_amount']:,} VNĐ ({r['items']})" for r in rows]
            return f"Danh sách đơn hàng của User #{user_id}:\n" + "\n".join(orders)
        return f"Không tìm thấy đơn hàng nào cho User #{user_id}."
    except Exception as e:
        return f"LỖI TRUY VẤN SQLITE (get_user_orders): {str(e)}"


def get_order_details(order_code: str) -> str:
    """
    Retrieve detailed information of an order from the SQLite database.

    Args:
        order_code (str):
            Unique order code.
            Example: "ORD-2024-001"

    Returns:
        str:
            Success:
                Human-readable order information.

            Failure:
                "LỖI: Mã đơn hàng không được để trống."
                "LỖI: Không tìm thấy đơn hàng ..."
                "LỖI TRUY VẤN SQLITE: ..."

    Database:
        - orders
        - order_items
        - products

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
    """

    if not order_code or not order_code.strip():
        return "LỖI: Mã đơn hàng không được để trống."

    code = order_code.strip().upper()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.order_code,
                o.user_id,
                o.status,
                o.total_amount,
                o.payment_method,
                o.shipping_address,
                o.created_at,
                GROUP_CONCAT(
                    p.name || ' (x' || oi.quantity || ')',
                    ', '
                ) AS items
            FROM orders o
            JOIN order_items oi
                ON o.id = oi.order_id
            JOIN products p
                ON oi.product_id = p.id
            WHERE o.order_code = ?
            GROUP BY o.id;
        """, (code,))

        order = cursor.fetchone()
        conn.close()

        if order is None:
            return f"LỖI: Không tìm thấy đơn hàng '{code}'."

        return (
            f"📦 ĐƠN HÀNG {order['order_code']}\n"
            f"- User ID: {order['user_id']}\n"
            f"- Trạng thái: {order['status']}\n"
            f"- Sản phẩm: {order['items']}\n"
            f"- Tổng tiền: {order['total_amount']:,.0f} VNĐ\n"
            f"- Thanh toán: {order['payment_method']}\n"
            f"- Địa chỉ: {order['shipping_address']}\n"
            f"- Ngày tạo: {order['created_at']}"
        )

    except sqlite3.Error as e:
        return f"LỖI TRUY VẤN SQLITE: {e}"

    except Exception as e:
        return f"LỖI: {e}"

def cancel_order(order_code: str, reason: str = "Đổi ý không mua nữa") -> str:
    """Hủy đơn hàng nếu đơn ở trạng thái PENDING hoặc CONFIRMED."""
    """
Cancel an order if it is still cancellable.

Business Rules:
    - Order must exist.
    - Only PENDING or CONFIRMED orders can be cancelled.

Args:
    order_code (str):
        Order code.

    reason (str, optional):
        Cancellation reason.

Returns:
    str:
        Cancellation result.

Database:
    - orders

Error Contract:
    Never raises exceptions.
"""
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
    """
Search products by keyword.

Args:
    keyword (str):
        Product name keyword.

Returns:
    str:
        Matching products or readable error.

Database:
    - products

Error Contract:
    Never raises exceptions.
"""
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
    """
    Retrieve shipping information of an order.

    Args:
        order_code (str):
            Order code.

    Returns:
        str:
            Shipping information or readable error.

    Database:
        - orders
        - shipping

    Error Contract:
        Never raises exceptions.
    """

    if not order_code or not order_code.strip():
        return "LỖI: Mã đơn hàng không được để trống."

    code = order_code.strip().upper()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.carrier,
                s.tracking_number,
                s.status,
                s.delivered_at
            FROM shipping s
            JOIN orders o
                ON s.order_id = o.id
            WHERE o.order_code = ?;
        """, (code,))

        shipping = cursor.fetchone()
        conn.close()

        if shipping is None:
            return f"LỖI: Không tìm thấy thông tin vận chuyển của '{code}'."

        delivered = (
            shipping["delivered_at"]
            if shipping["delivered_at"]
            else "Chưa giao"
        )

        return (
            f"🚚 VẬN CHUYỂN {code}\n"
            f"- Đơn vị: {shipping['carrier']}\n"
            f"- Tracking: {shipping['tracking_number']}\n"
            f"- Trạng thái: {shipping['status']}\n"
            f"- Giao lúc: {delivered}"
        )

    except sqlite3.Error as e:
        return f"LỖI TRUY VẤN SQLITE: {e}"

    except Exception as e:
        return f"LỖI: {e}"
# --- GROUP 3: APIS ĐỔI TRẢ HÀNG (CUSTOMER) ---

def check_return_eligibility(order_code: str) -> str:
    """
    Kiểm tra điều kiện đổi trả đơn hàng dựa trên trạng thái đơn hàng và chính sách 7 ngày.
    """
    code = order_code.strip().upper()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.status AS order_status,
                s.status AS shipping_status,
                s.delivered_at
            FROM orders o
            LEFT JOIN shipping s ON o.id = s.order_id
            WHERE o.order_code = ?;
        """, (code,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return f"LỖI: Không tìm thấy đơn hàng '{code}'."

        order_status = row["order_status"]

        # Nếu đơn hàng không ở trạng thái DELIVERED / RETURN_REQUESTED / RETURNING
        if order_status not in ["DELIVERED", "RETURN_REQUESTED", "RETURNING"]:
            return (
                f"❌ KHÔNG HỢP LỆ ĐỔI TRẢ\n"
                f"- Trạng thái đơn hiện tại: {order_status}\n"
                f"- Yêu cầu chính sách: Đơn hàng phải ở trạng thái DELIVERED (Đã giao thành công) mới được đổi trả."
            )

        delivered_at_str = row["delivered_at"]
        days = None
        if delivered_at_str:
            try:
                delivered_dt = datetime.strptime(delivered_at_str, "%Y-%m-%d %H:%M:%S")
                days = (datetime.now() - delivered_dt).days
            except Exception:
                days = 0

        # Nếu có mốc thời gian giao hàng và đã vượt quá 7 ngày (VD: test case ORD-9999)
        if days is not None and days > 7:
            return (
                f"❌ KHÔNG HỢP LỆ ĐỔI TRẢ\n"
                f"- Trạng thái đơn: {order_status}\n"
                f"- Đã giao {days} ngày\n"
                f"- Lý do: Vượt quá chính sách đổi trả 7 ngày"
            )

        delivered_info = f"Đã giao {days} ngày" if (days is not None and days >= 0) else "Đã giao thành công"
        return (
            f"✅ HỢP LỆ ĐỔI TRẢ\n"
            f"- Trạng thái đơn: {order_status}\n"
            f"- Tình trạng: {delivered_info}\n"
            f"- Chính sách: Đủ điều kiện khởi tạo ticket đổi trả 7 ngày."
        )

    except sqlite3.Error as e:
        return f"LỖI TRUY VẤN SQLITE: {e}"

    except Exception as e:
        return f"LỖI: {e}"
    
def create_return_request(order_code: str, reason: str = "DEFECTIVE", description: str = "Khách hàng đổi trả") -> str:
    """Khởi tạo đơn đổi trả trong bảng return_requests SQLite."""
    """
Create a return request for an eligible order.

Business Rules:
    - Order must satisfy return policy.
    - Create a new return request.

Args:
    order_code (str):
        Order code.

    reason (str, optional):
        Return reason.

    description (str, optional):
        Additional description.

Returns:
    str:
        Return request creation result.

Database:
    - orders
    - return_requests

Error Contract:
    Never raises exceptions.
"""
    code = order_code.strip().upper()
    check_res = check_return_eligibility(code)
    if "HỢP LỆ ĐỔI TRẢ" not in check_res:
        return f"TẠO ĐỔI TRẢ THẤT BẠI: {check_res}"
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, user_id FROM orders WHERE order_code = ?;", (code,))
        o = cursor.fetchone()
        if not o:
            conn.close()
            return f"LỖI: Không tìm thấy đơn hàng '{code}'."
            
        # Kiểm tra xem đơn hàng đã có yêu cầu đổi trả nào đang hoạt động chưa
        cursor.execute("SELECT return_code, status FROM return_requests WHERE order_id = ? AND status NOT IN ('CANCELLED', 'REJECTED');", (o["id"],))
        existing_ret = cursor.fetchone()
        if existing_ret:
            conn.close()
            return f"⚠️ ĐƠN HÀNG ĐÃ CÓ ĐƠN ĐỔI TRẢ: Mã đổi trả '{existing_ret['return_code']}' đang ở trạng thái {existing_ret['status']}."

        ret_code = f"RET-{random.randint(1000, 9999)}"
        valid_reason = reason.upper() if reason.upper() in ['DEFECTIVE', 'WRONG_ITEM', 'DAMAGED', 'MIND_CHANGE'] else 'DEFECTIVE'
        
        cursor.execute("""
            INSERT INTO return_requests (return_code, order_id, user_id, reason, description, status)
            VALUES (?, ?, ?, ?, ?, 'REQUESTED');
        """, (ret_code, o["id"], o["user_id"], valid_reason, description))
        
        cursor.execute("""
            UPDATE orders 
            SET status = 'RETURN_REQUESTED', updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?;
        """, (o["id"],))
        
        conn.commit()
        conn.close()
        
        return (
            f"✅ TẠO YÊU CẦU ĐỔI TRẢ THÀNH CÔNG (SQLITE)!\n"
            f"- Mã yêu cầu: {ret_code}\n"
            f"- Đơn hàng: {code}\n"
            f"- Lý do: {valid_reason} ({description})\n"
            f"- Trạng thái: REQUESTED (Đã gửi bộ phận Admin duyệt)."
        )
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (create_return_request): {str(e)}"


def get_return_request_status(order_code: str) -> str:
    """Tra cứu tiến độ đơn đổi trả trong SQLite."""
    """
Retrieve return request information.

Args:
    order_code (str):
        Order code or return code.

Returns:
    str:
        Return request status.

Database:
    - return_requests
    - orders

Error Contract:
    Never raises exceptions.
"""
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
    """
Cancel a return request.

Business Rules:
    - Request must exist.
    - Only REQUESTED status can be cancelled.

Args:
    return_id (str):
        Return request code.

Returns:
    str:
        Cancellation result.

Database:
    - return_requests

Error Contract:
    Never raises exceptions.
"""
    rid = return_id.strip().upper()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM return_requests WHERE return_code = ?;", (rid,))
        r = cursor.fetchone()
        
        if not r:
            conn.close()
            return f"LỖI: Không tìm thấy mã yêu cầu đổi trả '{return_id}'."
            
        if r["status"] in ["REQUESTED", "REVIEWING"]:
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
    """
Retrieve customer profile information.

Args:
    user_id (int):
        Customer ID.

Returns:
    str:
        User profile information.

Database:
    - users

Error Contract:
    Never raises exceptions.
"""
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
    """
Add a new product to the catalog.

Business Rules:
    - Caller must have ADMIN role.

Args:
    admin_id (int):
        Administrator ID.

    name (str):
        Product name.

    category_id (int):
        Product category.

    price (float):
        Product price.

    stock (int):
        Initial inventory.

    description (str, optional):
        Product description.

Returns:
    str:
        Product creation result.

Database:
    - users
    - products

Error Contract:
    Never raises exceptions.
"""
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
    """
Update product inventory.

Business Rules:
    - Caller must have ADMIN role.

Args:
    admin_id (int):
        Administrator ID.

    product_id (int):
        Product ID.

    new_stock (int):
        Updated inventory quantity.

Returns:
    str:
        Update result.

Database:
    - users
    - products

Error Contract:
    Never raises exceptions.
"""
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
    """
Update order status.

Business Rules:
    - Caller must have ADMIN role.
    - Status must be valid.

Args:
    admin_id (int):
        Administrator ID.

    order_code (str):
        Order code.

    new_status (str):
        Target order status.

Returns:
    str:
        Update result.

Database:
    - users
    - orders

Error Contract:
    Never raises exceptions.
"""
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
    """
Approve or reject a return request.

Business Rules:
    - Caller must have ADMIN role.
    - Action must be APPROVE or REJECT.

Args:
    admin_id (int):
        Administrator ID.

    return_code (str):
        Return request code.

    action (str):
        APPROVE or REJECT.

    note (str, optional):
        Admin note.

Returns:
    str:
        Review result.

Database:
    - users
    - return_requests

Error Contract:
    Never raises exceptions.
"""
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
        
        # 1. Kiểm tra trạng thái hiện tại của đơn đổi trả
        cursor.execute("SELECT status, description FROM return_requests WHERE return_code = ?;", (rcode,))
        r = cursor.fetchone()
        if not r:
            conn.close()
            return f"LỖI: Không tìm thấy mã yêu cầu đổi trả '{rcode}'."
            
        current_status = r["status"]
        if current_status in ["APPROVED", "REJECTED", "COMPLETED", "CANCELLED"]:
            conn.close()
            return f"❌ ĐƠN ĐÃ ĐƯỢC XỬ LÝ: Yêu cầu đổi trả '{rcode}' đã ở trạng thái '{current_status}', không thể xử lý lại."
            
        # 2. Xóa các ghi chú cũ nếu có để tránh bị lặp chuỗi "Admin Note: ..."
        orig_desc = r["description"] or ""
        base_desc = orig_desc.split(" | Admin Note:")[0]
        new_desc = f"{base_desc} | Admin Note: {note}"
        
        cursor.execute("""
            UPDATE return_requests 
            SET status = ?, description = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE return_code = ?;
        """, (target_status, new_desc, rcode))
        
        if target_status == "APPROVED":
            cursor.execute("""
                UPDATE orders SET status = 'RETURNING', updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT order_id FROM return_requests WHERE return_code = ?);
            """, (rcode,))
        elif target_status == "REJECTED":
            cursor.execute("""
                UPDATE orders SET status = 'DELIVERED', updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT order_id FROM return_requests WHERE return_code = ?);
            """, (rcode,))
        
        conn.commit()
        conn.close()
        return f"✅ DUYỆT ĐỔI TRẢ THÀNH CÔNG (ADMIN)! Yêu cầu '{rcode}' đã chuyển sang trạng thái '{target_status}'."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (review_return_request): {str(e)}"


def get_admin_dashboard_summary(admin_id: int = 3) -> str:
    """Admin: Xem báo cáo thống kê tổng quan (Đơn hàng, Đổi trả chờ duyệt, Sản phẩm, Doanh thu)."""
    """
Retrieve dashboard statistics for administrators.

Business Rules:
    - Caller must have ADMIN role.

Args:
    admin_id (int):
        Administrator ID.

Returns:
    str:
        Dashboard summary including:
            - Total orders
            - Pending return requests
            - Product count
            - Revenue

Database:
    - users
    - orders
    - return_requests
    - products

Error Contract:
    Never raises exceptions.
"""
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
