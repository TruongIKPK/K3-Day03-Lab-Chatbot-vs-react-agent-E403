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
    """
    Create a new customer order and simulate payment.

    Business Rules:
        - Product must exist.
        - Product must have sufficient stock.
        - Create order and order items.
        - Deduct inventory.
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
        str

        Success:
            Order confirmation.

        Failure:
            Product not found.
            Insufficient stock.
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
            VALUES (?, ?, ?, 30000, 'CONFIRMED', ?, ?);
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
    """
    Retrieve all orders of a customer.

    Business Rules:
        - Retrieve orders belonging to the specified customer.
        - Optionally filter by status.

    Args:
        user_id (int):
            Customer ID.

        status_filter (str, optional):
            Order status filter.
            Default = "ALL".

    Returns:
        str

        Success:
            List of matching orders.

        Failure:
            No orders found.
            SQLite execution error.

    Database:
        - orders
        - order_items
        - products

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    Retrieve detailed information about an order.

    Business Rules:
        - Order code must not be empty.
        - Order must exist.

    Args:
        order_code (str):
            Unique order code.

    Returns:
        str

        Success:
            Complete order information.

        Failure:
            Invalid order code.
            Order not found.
            SQLite execution error.

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
    """
    Cancel an order.

    Business Rules:
        - Order must exist.
        - Only PENDING or CONFIRMED orders can be cancelled.

    Args:
        order_code (str):
            Order code.

        reason (str, optional):
            Cancellation reason.

    Returns:
        str

        Success:
            Order cancelled successfully.

        Failure:
            Order not found.
            Order cannot be cancelled.
            SQLite execution error.

    Database:
        - orders

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Search products by keyword.

    Business Rules:
        - Search product names using partial matching.

    Args:
        keyword (str):
            Product keyword.

    Returns:
        str

        Success:
            Matching products.

        Failure:
            No products found.
            SQLite execution error.

    Database:
        - products

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    Retrieve shipping status of an order.

    Business Rules:
        - Order code must not be empty.
        - Shipping record must exist.

    Args:
        order_code (str):
            Order code.

    Returns:
        str

        Success:
            Shipping information.

        Failure:
            Order not found.
            Shipping information unavailable.
            SQLite execution error.

    Database:
        - orders
        - shipping

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
    Check whether an order is eligible for return.

    Business Rules:
        - Order must exist.
        - Order status must be DELIVERED.
        - Shipping status must be DELIVERED.
        - Delivery date must be within 7 days.

    Args:
        order_code (str):
            Order code.

    Returns:
        str

        Success:
            Return eligibility result.

        Failure:
            Order not found.
            Return policy not satisfied.
            SQLite execution error.

    Database:
        - orders
        - shipping

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
                o.status AS order_status,
                s.status AS shipping_status,
                s.delivered_at,
                CAST(
                    julianday('now') - julianday(s.delivered_at)
                    AS INTEGER
                ) AS days_since_delivery
            FROM orders o
            LEFT JOIN shipping s
                ON o.id = s.order_id
            WHERE o.order_code = ?;
        """, (code,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return f"LỖI: Không tìm thấy đơn hàng '{code}'."

        if row["order_status"] != "DELIVERED":
            return (
                "KHÔNG HỢP LỆ ĐỔI TRẢ: "
                f"Đơn đang ở trạng thái {row['order_status']}."
            )

        if row["shipping_status"] != "DELIVERED":
            return (
                "KHÔNG HỢP LỆ ĐỔI TRẢ: "
                "Đơn chưa giao thành công."
            )

        days = row["days_since_delivery"]

        if days is None:
            return "LỖI: Không xác định được ngày giao hàng."

        if days <= 7:
            return (
                f"✅ HỢP LỆ ĐỔI TRẢ\n"
                f"- Đã giao {days} ngày\n"
                f"- Chính sách: Trong 7 ngày"
            )

        return (
            f"❌ KHÔNG HỢP LỆ ĐỔI TRẢ\n"
            f"- Đã giao {days} ngày\n"
            f"- Vượt quá chính sách 7 ngày"
        )

    except sqlite3.Error as e:
        return f"LỖI TRUY VẤN SQLITE: {e}"

    except Exception as e:
        return f"LỖI: {e}"
    
def create_return_request(order_code: str, reason: str = "DEFECTIVE", description: str = "Khách hàng đổi trả") -> str:
    """
    Create a return request.

    Business Rules:
        - Order must satisfy return policy.
        - Only one active return request is allowed per order.

    Args:
        order_code (str):
            Order code.

        reason (str, optional):
            Return reason.

        description (str, optional):
            Additional description.

    Returns:
        str

        Success:
            Return request created.

        Failure:
            Order not eligible.
            Duplicate request.
            SQLite execution error.

    Database:
        - orders
        - return_requests

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Retrieve return request information.

    Business Rules:
        - Search by order code or return code.

    Args:
        order_code (str):
            Order code or return code.

    Returns:
        str

        Success:
            Return request information.

        Failure:
            Request not found.
            SQLite execution error.

    Database:
        - return_requests
        - orders

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Cancel a return request.

    Business Rules:
        - Return request must exist.
        - Only REQUESTED or REVIEWING requests can be cancelled.

    Args:
        return_id (str):
            Return request code.

    Returns:
        str

        Success:
            Return request cancelled.

        Failure:
            Request not found.
            Request cannot be cancelled.
            SQLite execution error.

    Database:
        - return_requests

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Retrieve customer profile.

    Business Rules:
        - User must exist.

    Args:
        user_id (int):
            Customer ID.

    Returns:
        str

        Success:
            Customer profile.

        Failure:
            User not found.
            SQLite execution error.

    Database:
        - users

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Add a new product.

    Business Rules:
        - Caller must have ADMIN role.

    Args:
        admin_id (int):
            Administrator ID.

        name (str):
            Product name.

        category_id (int):
            Category ID.

        price (float):
            Product price.

        stock (int):
            Initial stock quantity.

        description (str, optional):
            Product description.

    Returns:
        str

        Success:
            Product created.

        Failure:
            Permission denied.
            SQLite execution error.

    Database:
        - users
        - products

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Update product inventory.

    Business Rules:
        - Caller must have ADMIN role.
        - Product must exist.

    Args:
        admin_id (int):
            Administrator ID.

        product_id (int):
            Product ID.

        new_stock (int):
            Updated stock quantity.

    Returns:
        str

        Success:
            Inventory updated.

        Failure:
            Permission denied.
            Product not found.
            SQLite execution error.

    Database:
        - users
        - products

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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

    """
    Update an order status.

    Business Rules:
        - Caller must have ADMIN role.
        - Order must exist.
        - Target status must be valid.

    Args:
        admin_id (int):
            Administrator ID.

        order_code (str):
            Order code.

        new_status (str):
            Target status.

    Returns:
        str

        Success:
            Order status updated.

        Failure:
            Permission denied.
            Invalid status.
            Order not found.
            SQLite execution error.

    Database:
        - users
        - orders

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
    """
    Approve or reject a return request.

    Business Rules:
        - Caller must have ADMIN role.
        - Request must exist.
        - Request must not have been processed.
        - Action must be APPROVE or REJECT.

    Args:
        admin_id (int):
            Administrator ID.

        return_code (str):
            Return request code.

        action (str):
            APPROVE or REJECT.

        note (str, optional):
            Administrator note.

    Returns:
        str

        Success:
            Request reviewed successfully.

        Failure:
            Permission denied.
            Invalid action.
            Request not found.
            SQLite execution error.

    Database:
        - users
        - return_requests

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
        
        conn.commit()
        conn.close()
        return f"✅ DUYỆT ĐỔI TRẢ THÀNH CÔNG (ADMIN)! Yêu cầu '{rcode}' đã chuyển sang trạng thái '{target_status}'."
    except Exception as e:
        return f"LỖI THỰC THI SQLITE (review_return_request): {str(e)}"


def get_admin_dashboard_summary(admin_id: int = 3) -> str:
    """
    Retrieve administrator dashboard summary.

    Business Rules:
        - Caller must have ADMIN role.

    Args:
        admin_id (int):
            Administrator ID.

    Returns:
        str

        Success:
            Dashboard statistics.

        Failure:
            Permission denied.
            SQLite execution error.

    Database:
        - users
        - orders
        - products
        - return_requests

    Error Contract:
        Never raises exceptions.
        Always returns a readable string.
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
