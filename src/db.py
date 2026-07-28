"""
🗄️ DATABASE CONNECTION & INITIALIZATION MODULE (SQLite)
Quản lý kết nối SQLite và tạo CSDL 11 bảng với dữ liệu mẫu (Khách hàng & Admin).
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ecommerce.db")

def get_connection():
    """Tạo kết nối tới cơ sở dữ liệu SQLite ecommerce.db"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo 11 bảng CSDL và nạp dữ liệu mẫu nếu DB chưa tồn tại"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        role TEXT CHECK(role IN ('CUSTOMER', 'ADMIN', 'STAFF')) DEFAULT 'CUSTOMER',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES categories(id),
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        image_url TEXT,
        status TEXT CHECK(status IN ('ACTIVE', 'INACTIVE', 'OUT_OF_STOCK')) DEFAULT 'ACTIVE'
    );

    CREATE TABLE IF NOT EXISTS carts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id INTEGER REFERENCES carts(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER DEFAULT 1,
        price REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        order_code TEXT UNIQUE NOT NULL,
        total_amount REAL NOT NULL,
        shipping_fee REAL DEFAULT 0,
        status TEXT CHECK(status IN ('PENDING', 'CONFIRMED', 'PACKING', 'SHIPPING', 'DELIVERED', 'CANCELLED')) DEFAULT 'PENDING',
        payment_method TEXT,
        shipping_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER REFERENCES orders(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER DEFAULT 1,
        unit_price REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS shipping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER UNIQUE REFERENCES orders(id),
        carrier TEXT NOT NULL,
        tracking_number TEXT UNIQUE NOT NULL,
        status TEXT CHECK(status IN ('CREATED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'FAILED')) DEFAULT 'CREATED',
        estimated_delivery TIMESTAMP,
        delivered_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS return_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        return_code TEXT UNIQUE NOT NULL,
        order_id INTEGER REFERENCES orders(id),
        user_id INTEGER REFERENCES users(id),
        reason TEXT CHECK(reason IN ('DEFECTIVE', 'WRONG_ITEM', 'DAMAGED', 'MIND_CHANGE')) NOT NULL,
        description TEXT,
        status TEXT CHECK(status IN ('REQUESTED', 'REVIEWING', 'APPROVED', 'REJECTED', 'RETURNING', 'COMPLETED', 'CANCELLED')) DEFAULT 'REQUESTED',
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER REFERENCES chat_sessions(id),
        role TEXT CHECK(role IN ('USER', 'ASSISTANT', 'SYSTEM')) NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Đảm bảo tài khoản Admin (ID=3) luôn tồn tại
    cursor.execute("INSERT OR IGNORE INTO users (id, full_name, email, password, phone, role) VALUES (3, 'Admin Quản Lý Kho', 'admin@store.com', 'adminpass', '0900000000', 'ADMIN');")

    # Kiểm tra nếu chưa có đơn hàng mẫu thì chèn Seed Data
    cursor.execute("SELECT COUNT(*) FROM orders;")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        three_days_ago = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        fifteen_days_ago = (now - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Customers
        cursor.execute("INSERT OR IGNORE INTO users (id, full_name, email, password, phone, role) VALUES (1, 'Nguyễn Văn A', 'nguyenvana@gmail.com', 'pass123', '0987654321', 'CUSTOMER');")
        cursor.execute("INSERT OR IGNORE INTO users (id, full_name, email, password, phone, role) VALUES (2, 'Trần Thị B', 'tranthib@gmail.com', 'pass456', '0912345678', 'CUSTOMER');")
        
        # 2. Categories & Products
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, description) VALUES (1, 'Thời trang Nam', 'Trang phục nam');")
        cursor.execute("INSERT OR IGNORE INTO products (id, category_id, name, description, price, stock, status) VALUES (101, 1, 'Áo Polo Nam Premium', 'Vải thun CVC', 610000, 45, 'ACTIVE');")
        cursor.execute("INSERT OR IGNORE INTO products (id, category_id, name, description, price, stock, status) VALUES (102, 1, 'Tai nghe Bluetooth Noise Cancelling', 'Khử ồn', 3500000, 12, 'ACTIVE');")
        cursor.execute("INSERT OR IGNORE INTO products (id, category_id, name, description, price, stock, status) VALUES (103, 1, 'Giày Sneaker Thể Thao', 'Đế cao su', 890000, 0, 'OUT_OF_STOCK');")

        # 3. Orders
        cursor.execute("INSERT OR IGNORE INTO orders (id, user_id, order_code, total_amount, shipping_fee, status, payment_method, shipping_address) VALUES (1, 1, 'ORD-8899', 1250000, 30000, 'DELIVERED', 'COD', '123 Nguyễn Huệ, Quận 1, TP.HCM');")
        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, unit_price) VALUES (1, 101, 2, 610000);")
        cursor.execute("INSERT OR IGNORE INTO shipping (order_id, carrier, tracking_number, status, delivered_at) VALUES (1, 'Giao Hàng Nhanh (GHN)', 'GHN88992211', 'DELIVERED', ?);", (three_days_ago,))

        cursor.execute("INSERT OR IGNORE INTO orders (id, user_id, order_code, total_amount, shipping_fee, status, payment_method, shipping_address) VALUES (2, 1, 'ORD-1024', 3500000, 0, 'DELIVERED', 'VNPAY', '456 Lê Lợi, Quận 1, TP.HCM');")
        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, unit_price) VALUES (2, 102, 1, 3500000);")
        cursor.execute("INSERT OR IGNORE INTO shipping (order_id, carrier, tracking_number, status, delivered_at) VALUES (2, 'Giao Hàng Tiết Kiệm (GHTK)', 'GHTK102499', 'DELIVERED', ?);", (fifteen_days_ago,))

        cursor.execute("INSERT OR IGNORE INTO orders (id, user_id, order_code, total_amount, shipping_fee, status, payment_method, shipping_address) VALUES (3, 2, 'ORD-5500', 890000, 30000, 'PENDING', 'COD', '789 Điện Biên Phủ, Bình Thạnh, TP.HCM');")
        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, unit_price) VALUES (3, 103, 1, 890000);")
        cursor.execute("INSERT OR IGNORE INTO shipping (order_id, carrier, tracking_number, status) VALUES (3, 'Viettel Post', 'VT55001122', 'CREATED');")

    conn.commit()
    conn.close()

# --- CHAT SESSION & MEMORY MANAGEMENT (LƯU NGỮ CẢNH HỘI THOẠI) ---

def get_or_create_session(user_id: int, session_id: int = None) -> int:
    """Tạo mới hoặc lấy session_id hội thoại đang hoạt động của user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute("SELECT id FROM chat_sessions WHERE id = ?;", (int(session_id),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return int(session_id)
            
    # Lấy phiên thoại mới nhất của user_id nếu chưa truyền session_id
    cursor.execute("SELECT id FROM chat_sessions WHERE user_id = ? ORDER BY id DESC LIMIT 1;", (int(user_id),))
    row = cursor.fetchone()
    if row:
        sid = row["id"]
        conn.close()
        return sid
        
    # Tạo phiên thoại mới nếu chưa có
    cursor.execute("INSERT INTO chat_sessions (user_id) VALUES (?);", (int(user_id),))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def save_chat_message(session_id: int, role: str, message: str) -> None:
    """Lưu tin nhắn (USER / ASSISTANT) vào bảng chat_messages SQLite."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, message)
            VALUES (?, ?, ?);
        """, (int(session_id), role.upper(), message))
        
        # Cập nhật thời gian updated_at cho phiên thoại
        cursor.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (int(session_id),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Lỗi lưu chat message: {e}")


def get_chat_history(session_id: int, limit: int = 6) -> list:
    """Lấy danh sách tin nhắn gần đây trong phiên thoại để tái tạo ngữ cảnh."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, message, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?;
        """, (int(session_id), int(limit)))
        rows = cursor.fetchall()
        conn.close()
        # Đảo ngược lại theo thứ tự thời gian từ cũ -> mới
        return [dict(r) for r in reversed(rows)]
    except Exception:
        return []


def extract_order_code_from_history(session_id: int) -> str:
    """Truy tìm mã đơn hàng (ORD-xxxx) gần nhất trong lịch sử hội thoại của phiên thoại."""
    import re
    history = get_chat_history(session_id, limit=10)
    for msg in reversed(history):
        match = re.search(r"ORD-\d+", msg.get("message", "").upper())
        if match:
            return match.group(0)
    return None


if __name__ == "__main__":
    init_db()
    print("✅ Đã khởi tạo và cập nhật cơ sở dữ liệu SQLite thành công!")
