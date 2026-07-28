"""
🚀 FLASK WEB SERVER FOR E-COMMERCE AI ASSISTANT & ADMIN DASHBOARD
Phục vụ giao diện Web App HTML/CSS/JS, Đăng nhập/Đăng ký, Đặt hàng & REST APIs kết nối CSDL SQLite.
"""

import os
import sys
import re
from flask import Flask, render_template, request, jsonify

# Thêm đường dẫn src vào sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import (
    get_connection,
    init_db,
    get_or_create_session,
    save_chat_message,
    get_chat_history,
    extract_order_code_from_history
)
from tools import (
    AVAILABLE_TOOLS,
    create_order,
    get_user_orders,
    get_order_details,
    cancel_order,
    get_shipping_status,
    check_return_eligibility,
    create_return_request,
    cancel_return_request,
    get_return_request_status,
    get_user_profile,
    add_product,
    update_product_stock,
    update_order_status,
    review_return_request,
    get_admin_dashboard_summary
)
from providers import get_llm_provider
from prompts import REACT_SYSTEM_PROMPT, CHATBOT_BASELINE_PROMPT, check_guardrails

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Khởi tạo CSDL SQLite
init_db()

@app.route("/")
def index():
    """Trang chủ Giao diện FE Web App"""
    return render_template("index.html")


# --- API AUTHENTICATION (ĐĂNG NHẬP & ĐĂNG KÝ) ---

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """Đăng ký tài khoản người dùng mới (Customer hoặc Admin)"""
    data = request.json or {}
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    phone = data.get("phone", "").strip()
    role = data.get("role", "CUSTOMER").upper()
    
    if role not in ["CUSTOMER", "ADMIN"]:
        role = "CUSTOMER"
        
    if not full_name or not email or not password:
        return jsonify({"success": False, "message": "Vui lòng điền đầy đủ Họ tên, Email và Mật khẩu."})
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?;", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email này đã được sử dụng."})
            
        cursor.execute("""
            INSERT INTO users (full_name, email, password, phone, role)
            VALUES (?, ?, ?, ?, ?);
        """, (full_name, email, password, phone, role))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Đăng ký tài khoản thành công! (ID #{new_id})",
            "user": {
                "id": new_id,
                "full_name": full_name,
                "email": email,
                "role": role,
                "phone": phone
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi đăng ký: {str(e)}"})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """Đăng nhập hệ thống"""
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    
    if not email or not password:
        return jsonify({"success": False, "message": "Vui lòng nhập Email và Mật khẩu."})
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, full_name, email, phone, role FROM users WHERE LOWER(email) = ? AND password = ?;", (email, password))
        u = cursor.fetchone()
        conn.close()
        
        if u:
            return jsonify({
                "success": True,
                "message": "Đăng nhập thành công!",
                "user": dict(u)
            })
        else:
            return jsonify({"success": False, "message": "Email hoặc mật khẩu không chính xác!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"})


@app.route("/api/users", methods=["GET"])
def api_get_users():
    """Lấy danh sách người dùng trong hệ thống (Cho Admin)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, phone, role, created_at FROM users ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"users": [dict(r) for r in rows]})


# --- REST ENDPOINTS DỮ LIỆU ĐƠN HÀNG & SẢN PHẨM ---

@app.route("/api/orders/create", methods=["POST"])
def api_create_order():
    """Khách hàng chọn sản phẩm Đặt hàng và Giả lập Thanh toán"""
    data = request.json or {}
    user_id = data.get("user_id", 1)
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    payment_method = data.get("payment_method", "COD")
    shipping_address = data.get("shipping_address", "123 Nguyễn Huệ, Quận 1, TP.HCM")
    
    if not product_id:
        return jsonify({"success": False, "message": "Vui lòng chọn sản phẩm cần đặt hàng."})
        
    msg = create_order(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity,
        payment_method=payment_method,
        shipping_address=shipping_address
    )
    
    success = "🎉 ĐẶT HÀNG THÀNH CÔNG" in msg
    return jsonify({"success": success, "message": msg})


@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    """Lấy danh sách đơn hàng từ SQLite"""
    user_id = request.args.get("user_id", type=int)
    is_admin = request.args.get("is_admin", "false").lower() == "true"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_admin:
        query = """
            SELECT o.order_code, o.user_id, u.full_name AS user_name, o.status, o.total_amount, o.payment_method, o.created_at,
                   GROUP_CONCAT(p.name || ' (x' || oi.quantity || ')', ', ') AS items
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            GROUP BY o.id ORDER BY o.created_at DESC;
        """
        cursor.execute(query)
    else:
        query = """
            SELECT o.order_code, o.user_id, o.status, o.total_amount, o.payment_method, o.created_at,
                   GROUP_CONCAT(p.name || ' (x' || oi.quantity || ')', ', ') AS items
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = ?
            GROUP BY o.id ORDER BY o.created_at DESC;
        """
        cursor.execute(query, (user_id or 1,))
        
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"orders": [dict(r) for r in rows]})


@app.route("/api/returns", methods=["GET"])
def api_get_returns():
    """Lấy danh sách yêu cầu đổi trả từ SQLite"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.return_code, o.order_code, r.user_id, u.full_name AS user_name, r.reason, r.description, r.status, r.created_at
        FROM return_requests r
        JOIN orders o ON r.order_id = o.id
        LEFT JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC;
    """)
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"returns": [dict(r) for r in rows]})


@app.route("/api/products", methods=["GET"])
def api_get_products():
    """Lấy danh sách sản phẩm trong kho SQLite"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, status FROM products ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"products": [dict(r) for r in rows]})


@app.route("/api/admin/dashboard", methods=["GET"])
def api_admin_dashboard():
    """Lấy báo cáo thống kê Admin Dashboard Summary"""
    admin_id = request.args.get("admin_id", 3, type=int)
    conn = get_connection()
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
    
    return jsonify({
        "total_orders": total_orders,
        "pending_returns": pending_returns,
        "total_products": total_products,
        "revenue": revenue
    })


@app.route("/api/orders/cancel", methods=["POST"])
def api_cancel_order():
    """Khách hàng hủy đơn hàng (PENDING hoặc CONFIRMED)"""
    data = request.json or {}
    order_code = data.get("order_code", "").strip()
    reason = data.get("reason", "Khách hàng hủy từ Web App")
    if not order_code:
        return jsonify({"success": False, "message": "Vui lòng cung cấp mã đơn hàng cần hủy."})
    msg = cancel_order(order_code, reason)
    success = "HỦY ĐƠN THÀNH CÔNG" in msg
    return jsonify({"success": success, "message": msg})


@app.route("/api/returns/cancel", methods=["POST"])
def api_cancel_return():
    """Khách hàng hủy yêu cầu đổi trả đang chờ duyệt"""
    data = request.json or {}
    return_id = data.get("return_id", "").strip()
    if not return_id:
        return jsonify({"success": False, "message": "Vui lòng cung cấp mã yêu cầu đổi trả."})
    msg = cancel_return_request(return_id)
    success = "ĐÃ HỦY" in msg
    return jsonify({"success": success, "message": msg})


@app.route("/api/users/profile", methods=["GET"])
def api_user_profile():
    """Tra cứu thông tin cá nhân khách hàng"""
    user_id = request.args.get("user_id", 1, type=int)
    profile_info = get_user_profile(user_id)
    return jsonify({"success": True, "profile": profile_info})


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Xử lý tin nhắn từ FE với ReAct Agent Loop, Bộ Nhớ Context Session & Trích xuất Trace Log"""
    data = request.json or {}
    user_query = data.get("query", "")
    user_id = data.get("user_id", 1)
    user_role = data.get("role", "CUSTOMER")
    input_session_id = data.get("session_id")
    
    if not user_query:
        return jsonify({"response": "Vui lòng nhập câu hỏi.", "trace": [], "session_id": input_session_id})

    # Lấy hoặc tạo phiên thoại hội thoại
    session_id = get_or_create_session(user_id, input_session_id)

    provider = get_llm_provider()
    trace_steps = []
    
    # 1. Kiểm tra Phanh Guardrails (Chống tấn công ngoài phạm vi & vượt quyền)
    guard = check_guardrails(user_query, user_role)
    if not guard["safe"]:
        trace_steps.append({
            "thought": f"Phát hiện tin nhắn ngoài phạm vi hoặc vi phạm an toàn ({guard['type']}). Kích hoạt Phanh Scope Guardrail.",
            "action": "scope_guardrail_block",
            "observation": "Blocked by Scope Policy"
        })
        save_chat_message(session_id, "USER", user_query)
        save_chat_message(session_id, "ASSISTANT", guard["reason"])
        return jsonify({"response": guard["reason"], "trace": trace_steps, "session_id": session_id})

    # Trích xuất mã đơn hàng từ câu hỏi hiện tại HOẶC truy tìm từ bộ nhớ hội thoại trước đó
    order_match = re.search(r"ORD-\d+", user_query.upper())
    code = order_match.group(0) if order_match else None
    
    if not code:
        code_from_memory = extract_order_code_from_history(session_id)
        if code_from_memory:
            code = code_from_memory
            trace_steps.append({
                "thought": f"🧠 Tái tạo ngữ cảnh bộ nhớ (Session #{session_id}): Nhớ mã đơn hàng {code} từ tin nhắn trước.",
                "action": f"memory_recall['{code}']",
                "observation": f"Recalled {code} from context"
            })
    
    query_lower = user_query.lower()
    
    if ("hủy" in query_lower or "huy" in query_lower or "cancel" in query_lower) and code:
        res = cancel_order(code, "Yêu cầu từ AI Chatbot")
        trace_steps.append({
            "thought": f"Khách hàng muốn hủy đơn hàng {code} (Từ ngữ cảnh hội thoại). Kích hoạt tool cancel_order.",
            "action": f"cancel_order['{code}', 'Yêu cầu từ AI Chatbot']",
            "observation": res
        })
        final_res = f"📝 Thông báo xử lý hủy đơn <strong>{code}</strong>:<br>{res}"

    elif "đổi trả" in query_lower and code:
        eligibility = check_return_eligibility(code)
        trace_steps.append({
            "thought": f"Khách hàng hỏi đổi trả đơn {code} (Từ ngữ cảnh hội thoại). Dùng tool check_return_eligibility kiểm tra hạn 7 ngày.",
            "action": f"check_return_eligibility['{code}']",
            "observation": eligibility
        })
        
        if "HỢP LỆ ĐỔI TRẢ" in eligibility:
            create_res = create_return_request(code, "DEFECTIVE", f"Tạo tự động cho User #{user_id}")
            trace_steps.append({
                "thought": f"Đơn hàng {code} hợp lệ đổi trả. Kích hoạt tool create_return_request.",
                "action": f"create_return_request['{code}', 'DEFECTIVE']",
                "observation": create_res
            })
            final_res = f"✅ Đơn hàng <strong>{code}</strong> đủ điều kiện đổi trả!<br>{create_res}"
        else:
            final_res = f"⚠️ Không thể khởi tạo đổi trả:<br>{eligibility}"
            
    elif ("kiểm tra" in query_lower or "trạng thái" in query_lower or "giao chưa" in query_lower) and code:
        details = get_order_details(code)
        shipping = get_shipping_status(code)
        trace_steps.append({
            "thought": f"Truy vấn chi tiết đơn hàng {code} và vị trí vận chuyển.",
            "action": f"get_order_details['{code}']",
            "observation": details
        })
        trace_steps.append({
            "thought": f"Truy vấn hành trình vận chuyển.",
            "action": f"get_shipping_status['{code}']",
            "observation": shipping
        })
        final_res = f"📦 Thông tin đơn hàng <strong>{code}</strong>:<br><pre style='font-family:sans-serif;'>{details}\n\n{shipping}</pre>"
        
    elif "admin" in query_lower or "thống kê" in query_lower or "doanh thu" in query_lower:
        if user_role == "ADMIN":
            summary = get_admin_dashboard_summary(user_id)
            trace_steps.append({
                "thought": f"Xác nhận User #{user_id} có quyền ADMIN. Gọi tool get_admin_dashboard_summary.",
                "action": f"get_admin_dashboard_summary[{user_id}]",
                "observation": summary
            })
            final_res = f"<pre style='font-family:sans-serif;'>{summary}</pre>"
        else:
            trace_steps.append({
                "thought": f"Cảnh báo bảo mật: User #{user_id} là CUSTOMER nhưng yêu cầu xem dữ liệu Admin.",
                "action": "security_check",
                "observation": "Access Denied"
            })
            final_res = "🚫 TỪ CHỐI TRUY CẬP: Tài khoản của bạn không có quyền xem thông tin Admin."
    else:
        # Lấy lịch sử hội thoại 6 tin gần đây để làm Context cho LLM
        history_msgs = get_chat_history(session_id, limit=6)
        history_text = "\n".join([f"{m['role']}: {m['message']}" for m in history_msgs])
        context_prompt = f"Lịch sử hội thoại gần đây trong phiên:\n{history_text}\n\nCâu hỏi mới: {user_query}" if history_text else user_query

        llm_out = provider.generate(context_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        trace_steps.append({
            "thought": "Sinh phản hồi qua ReAct LLM Engine kết hợp bộ nhớ lịch sử hội thoại.",
            "action": "generate_response_with_memory",
            "observation": "Success"
        })
        final_res = llm_out

    # Lưu tin nhắn vào CSDL SQLite cho bộ nhớ phiên thoại
    save_chat_message(session_id, "USER", user_query)
    save_chat_message(session_id, "ASSISTANT", final_res)

    return jsonify({"response": final_res, "trace": trace_steps, "session_id": session_id})


@app.route("/api/admin/product", methods=["POST"])
def api_admin_add_product():
    """Admin thêm sản phẩm mới"""
    data = request.json or {}
    msg = add_product(
        admin_id=data.get("admin_id", 3),
        name=data.get("name", ""),
        category_id=data.get("category_id", 1),
        price=data.get("price", 0),
        stock=data.get("stock", 0),
        description=data.get("description", "")
    )
    return jsonify({"message": msg})


@app.route("/api/admin/order-status", methods=["POST"])
def api_admin_order_status():
    """Admin cập nhật trạng thái đơn hàng"""
    data = request.json or {}
    msg = update_order_status(
        admin_id=data.get("admin_id", 3),
        order_code=data.get("order_code", ""),
        new_status=data.get("new_status", "CONFIRMED")
    )
    return jsonify({"message": msg})


@app.route("/api/admin/review-return", methods=["POST"])
def api_admin_review_return():
    """Admin duyệt đổi trả"""
    data = request.json or {}
    msg = review_return_request(
        admin_id=data.get("admin_id", 3),
        return_code=data.get("return_code", ""),
        action=data.get("action", "APPROVE"),
        note=data.get("note", "Duyệt từ Web App Admin")
    )
    return jsonify({"message": msg})


if __name__ == "__main__":
    print("==================================================")
    print("🚀 FLASK WEB APP SERVER ĐANG CHẠY TẠI:")
    print("👉 http://127.0.0.1:5000")
    print("==================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
