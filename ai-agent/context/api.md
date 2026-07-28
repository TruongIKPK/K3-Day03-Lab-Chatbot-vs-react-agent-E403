# 🔌 DANH SÁCH TOOL & SPECIFICATION API HỆ THỐNG (API CONTEXT)

> Tài liệu quy định chi tiết tất cả các APIs / Tools mà ReAct Agent sử dụng để tương tác với Cơ sở dữ liệu E-Commerce 11 bảng, bao gồm luồng Khách hàng (Customer) và luồng Quản trị viên (Admin).

---

## 📐 TỔNG QUAN PHÂN LUỒNG API HỆ THỐNG

Các API được chia thành 5 nhóm chức năng chính:
1. **Group 1: Tra cứu & Quản lý Đơn hàng (Order Management APIs)**
2. **Group 2: Theo dõi Vận chuyển & Giao hàng (Shipping & Carrier APIs)**
3. **Group 3: Xử lý Yêu cầu Đổi trả & Bảo hành (Return Request APIs)**
4. **Group 4: Thông tin Người dùng & Phiên hội thoại (User & Chat Session APIs)**
5. **Group 5: Quản trị Hệ thống cho Admin (Admin Management APIs)** *(Bổ sung mới)*

---

## 🛠️ 1. GROUP 1: TRA CỨU & QUẢN LÝ ĐƠN HÀNG (ORDER APIS)

### 1.1 `get_user_orders(user_id: int, status_filter: str = "ALL") -> str`
- **Mục đích**: Tra cứu danh sách tất cả các đơn hàng gần đây của một khách hàng trong bảng `Order`.
- **Rest API Mapped**: `GET /api/v1/users/{user_id}/orders?status={status_filter}`

### 1.2 `get_order_details(order_code: str) -> str`
- **Mục đích**: Truy vấn thông tin chi tiết một đơn hàng từ bảng `Order` kết hợp `OrderItem`, `Product` và `User`.
- **Rest API Mapped**: `GET /api/v1/orders/{order_code}`

### 1.3 `cancel_order(order_code: str, reason: str) -> str`
- **Mục đích**: Hủy đơn hàng khi đơn chưa chuyển sang khâu đóng gói/vận chuyển (Chỉ cho phép khi `Order.status` là `PENDING` hoặc `CONFIRMED`).
- **Rest API Mapped**: `POST /api/v1/orders/{order_code}/cancel`

### 1.4 `search_products(keyword: str) -> str`
- **Mục đích**: Tra cứu thông tin sản phẩm, giá bán và số lượng tồn kho trong bảng `Product` & `Category`.
- **Rest API Mapped**: `GET /api/v1/products?q={keyword}`

---

## 🚚 2. GROUP 2: THEO DÕI VẬN CHUYỂN & GIAO HÀNG (SHIPPING APIS)

### 2.1 `get_shipping_status(order_code: str) -> str`
- **Mục đích**: Truy vấn dữ liệu vận chuyển liên kết giữa `Order` và `Shipping`.
- **Rest API Mapped**: `GET /api/v1/orders/{order_code}/shipping`

---

## 🔄 3. GROUP 3: XỬ LÝ YÊU CẦU ĐỔI TRẢ (RETURN REQUEST APIS)

### 3.1 `check_return_eligibility(order_code: str) -> str`
- **Mục đích**: Kiểm tra các điều kiện kinh doanh trước khi cho phép tạo đơn đổi trả.
- **Rest API Mapped**: `GET /api/v1/orders/{order_code}/return-eligibility`

### 3.2 `create_return_request(order_code: str, reason: str, description: str, image_url: str = "") -> str`
- **Mục đích**: Khởi tạo bản ghi đổi trả mới trong bảng `ReturnRequest` với trạng thái ban đầu là `REQUESTED`.
- **Rest API Mapped**: `POST /api/v1/return-requests`

### 3.3 `get_return_request_status(order_code: str) -> str`
- **Mục đích**: Tra cứu tiến độ xử lý của đơn đổi trả đã gửi trong bảng `ReturnRequest`.
- **Rest API Mapped**: `GET /api/v1/orders/{order_code}/return-request`

### 3.4 `cancel_return_request(return_id: str) -> str`
- **Mục đích**: Cho phép khách hàng hủy yêu cầu đổi trả nếu chưa duyệt (`status == REQUESTED`).
- **Rest API Mapped**: `POST /api/v1/return-requests/{return_id}/cancel`

---

## 👤 4. GROUP 4: THÔNG TIN KHÁCH HÀNG & PHIÊN CHAT (USER & CHAT APIS)

### 4.1 `get_user_profile(user_id: int) -> str`
- **Mục đích**: Tra cứu thông tin cá nhân khách hàng từ bảng `User`.
- **Rest API Mapped**: `GET /api/v1/users/{user_id}`

---

## 🔑 5. GROUP 5: QUẢN TRỊ HỆ THỐNG CHO ADMIN (ADMIN MANAGEMENT APIS)

### 5.1 `add_product(admin_id: int, name: str, category_id: int, price: float, stock: int, description: str = "") -> str`
- **Mục đích**: Cho phép Admin thêm sản phẩm mới vào danh mục sản phẩm (`Product`).
- **Phân quyền**: Yêu cầu `User.role == 'ADMIN'` (Ví dụ: `admin_id = 3`).
- **Rest API Mapped**: `POST /api/v1/admin/products`
- **Body Request Payload**:
  ```json
  {
    "admin_id": 3,
    "name": "Áo Sơ Mi Nam Công Sở",
    "category_id": 1,
    "price": 450000,
    "stock": 100,
    "description": "Chống nhăn cao cấp"
  }
  ```
- **Kết quả trả về**:
  - `✅ THÊM SẢN PHẨM THÀNH CÔNG: ID 104 - 'Áo Sơ Mi Nam Công Sở' (Giá: 450,000 VNĐ | Tồn kho: 100).`

---

### 5.2 `update_product_stock(admin_id: int, product_id: int, new_stock: int) -> str`
- **Mục đích**: Cập nhật số lượng tồn kho sản phẩm trong bảng `Product`.
- **Rest API Mapped**: `PATCH /api/v1/admin/products/{product_id}/stock`
- **Tham số**:
  - `admin_id` (int): ID của Admin thực hiện thao tác.
  - `product_id` (int): ID sản phẩm cần điều chỉnh kho.
  - `new_stock` (int): Số lượng tồn kho mới.
- **Kết quả trả về**:
  - `✅ CẬP NHẬT TỒN KHO THÀNH CÔNG: Sản phẩm #101 ('Áo Polo Nam Premium') -> Kho mới: 80 cái.`

---

### 5.3 `update_order_status(admin_id: int, order_code: str, new_status: str) -> str`
- **Mục đích**: Chuyển trạng thái đơn hàng (`PENDING` ➔ `CONFIRMED` ➔ `PACKING` ➔ `SHIPPING` ➔ `DELIVERED` ➔ `CANCELLED`).
- **Rest API Mapped**: `PATCH /api/v1/admin/orders/{order_code}/status`
- **Tham số**:
  - `admin_id` (int): ID của Admin.
  - `order_code` (str): Mã đơn hàng.
  - `new_status` (str): Trạng thái mới (Ví dụ: `'SHIPPING'`, `'DELIVERED'`).
- **Kết quả trả về**:
  - `✅ CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG THÀNH CÔNG: Đơn ORD-5500 chuyển sang SHIPPING.`

---

### 5.4 `review_return_request(admin_id: int, return_code: str, action: str, note: str = "") -> str`
- **Mục đích**: Admin phê duyệt (`APPROVED`) hoặc từ chối (`REJECTED`) yêu cầu đổi trả của khách hàng trong bảng `ReturnRequest`.
- **Rest API Mapped**: `POST /api/v1/admin/return-requests/{return_code}/review`
- **Tham số**:
  - `admin_id` (int): ID của Admin duyệt đơn.
  - `return_code` (str): Mã đơn đổi trả (VD: `'RET-5541'`).
  - `action` (str): `'APPROVE'` hoặc `'REJECT'`.
  - `note` (str): Ghi chú lý do duyệt/từ chối từ Admin.
- **Kết quả trả về**:
  - `✅ PHÊ DUYỆT ĐỔI TRẢ: Yêu cầu RET-5541 cho đơn ORD-8899 đã được APPROVED. Trạng thái tiếp theo: Khách gửi hàng về kho.`

---

### 5.5 `get_admin_dashboard_summary(admin_id: int) -> str`
- **Mục đích**: Thống kê số lượng đơn hàng, số yêu cầu đổi trả đang chờ duyệt (`REQUESTED`), tổng sản phẩm và tổng doanh thu.
- **Rest API Mapped**: `GET /api/v1/admin/dashboard`
- **Kết quả trả về**:
  - `📊 THỐNG KÊ ADMIN DASHBOARD: Tổng đơn hàng: 3 | Đơn chờ duyệt đổi trả: 1 | Tổng sản phẩm: 4 | Doanh thu: 5,640,000 VNĐ.`

---

## 📋 6. TỔNG HỢP REGISTRY 15 TOOLS REACT AGENT (`src/tools.py`)

```python
AVAILABLE_TOOLS = {
    # Khách hàng (Customer Tools)
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
    
    # Quản trị viên (Admin Tools)
    "add_product": add_product,
    "update_product_stock": update_product_stock,
    "update_order_status": update_order_status,
    "review_return_request": review_return_request,
    "get_admin_dashboard_summary": get_admin_dashboard_summary,
}
```
