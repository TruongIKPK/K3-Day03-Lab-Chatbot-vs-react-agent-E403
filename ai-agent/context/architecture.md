# 🏛️ KIẾN TRÚC HỆ THỐNG AGENT & PHÂN QUYỀN (SYSTEM ARCHITECTURE)

> Kiến trúc vòng lặp suy luận ReAct Agent, phân luồng Vai trò Khách hàng (Customer) vs Quản trị viên (Admin), tích hợp Tools và phanh an toàn (Safeguards).

---

## 🏗️ 1. SƠ ĐỒ KIẾN TRÚC PHÂN LUỒNG QUYỀN (RBAC ARCHITECTURE)

```mermaid
flowchart TD
    User[Người dùng / User Interface] -->|Nhập câu hỏi| Agent[ReAct Agent Engine]
    
    subgraph RBAC [Tầng Phân Quyền & Phân Luồng Role]
        Agent -->|Kiểm tra Vai trò| CheckRole{Role Check}
        CheckRole -->|Khách hàng Customer| CustTools[Customer Tool Registry]
        CheckRole -->|Quản trị viên Admin| AdminTools[Admin Tool Registry]
    end

    subgraph CustomerTools [Customer Tools (10 Tools)]
        CustTools --> T1[get_order_details]
        CustTools --> T2[get_shipping_status]
        CustTools --> T3[check_return_eligibility]
        CustTools --> T4[create_return_request]
        CustTools --> T5[get_user_orders]
        CustTools --> T6[cancel_order / search_products]
    end

    subgraph AdminToolsLayer [Admin Tools (5 Tools)]
        AdminTools --> A1[add_product]
        AdminTools --> A2[update_product_stock]
        AdminTools --> A3[update_order_status]
        AdminTools --> A4[review_return_request]
        AdminTools --> A5[get_admin_dashboard_summary]
    end

    subgraph DB [Database Layer]
        CustomerTools & AdminToolsLayer <--> SQLite[(SQLite CSDL 11 Bảng - ecommerce.db)]
    end

    subgraph Safeguards [Safeguards & Guardrails]
        SG1[Max Iteration Limit = 3]
        SG2[7-Day Return Policy Rule]
        SG3[Admin Auth Verification: User.role == 'ADMIN']
    end

    Agent <---> Safeguards
```

---

## 🔄 2. CHU TRÌNH THỰC THI ADMIN TOOL (VÍ DỤ DUYỆT ĐỔI TRẢ & THÊM SP)

1. **Admin gửi câu hỏi**: Admin nhập: *"Tôi muốn phê duyệt yêu cầu đổi trả RET-5541 và thêm sản phẩm Áo Sơ Mi Nam giá 450,000 VNĐ."*
2. **Thought Phase**: Agent nhận biết người dùng có quyền Admin (ID = 3), lựa chọn gọi tool `review_return_request` trước.
3. **Action Phase**: Agent phát lệnh `Action: review_return_request[admin_id=3, return_code="RET-5541", action="APPROVE", note="Đồng ý duyệt"]`.
4. **Observation Phase**: Hệ thống gọi `src/tools.py`, kiểm tra `User.role == 'ADMIN'`, cập nhật trạng thái `return_requests.status = 'APPROVED'` và trả về `Observation`.
5. **Next Action Phase**: Agent tiếp tục gọi `add_product[admin_id=3, name="Áo Sơ Mi Nam", category_id=1, price=450000, stock=100]`.
6. **Final Answer**: Agent tổng hợp kết quả gửi cho Admin.

---

## 🛡️ 3. PHANH AN TOÀN & BẢO MẬT PHÂN QUYỀN (SAFEGUARDS)

- **Role-Based Access Control (RBAC)**: Mọi Admin Tool trong `src/tools.py` đều bắt buộc gọi hàm kiểm tra `_verify_admin(conn, admin_id)`. Nếu `user_id` không thuộc nhóm `ADMIN`, hệ thống lập tức từ chối và trả về chuỗi `🚫 TỪ CHỐI QUYỀN`.
- **Max Iterations Limit**: Khống chế tối đa 3 vòng lặp ReAct nhằm ngăn chặn Agent rơi vào vòng lặp vô tận.
- **Strict Input Validation**: Kiểm tra mã đơn, tham số trạng thái đơn hàng và định dạng giá tiền trước khi ghi vào SQLite.
