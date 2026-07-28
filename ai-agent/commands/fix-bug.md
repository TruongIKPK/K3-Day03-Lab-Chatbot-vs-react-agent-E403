# 🛠️ COMMAND: FIX BUG

Lệnh hướng dẫn Agent sửa lỗi trong mã nguồn hoặc trong vòng lặp ReAct của bài toán Trợ lý Đơn hàng & Đổi trả.

## 📋 Scenario: Lỗi Logic "Không Hợp Lệ Đổi Trả"
**Mô tả sự cố**: Chatbot báo đơn hàng hợp lệ đổi trả dù đã giao 15 ngày (vượt ngưỡng 7 ngày).
**Mã lỗi liên quan**: `src/agent.py` (Lỗi tính toán `days_since_delivery` hoặc so sánh điều kiện).

## 🎯 Input Prompt (Gửi cho AI Agent)

```
You are the **Backend Code Repair Specialist** for the E-Commerce Order Assistant.

**BUG REPORT RECEIVED**:
- Error Type: Logic Bug (Rule Violation)
- Affected Code: `src/tools.py` or `src/agent.py`
- Symptom: User reports "Return request rejected" for order ORD-1024, stating "it was only 15 days ago". The system logic is incorrectly classifying this as ineligible.

**MISSION**: Fix the bug in the code logic.

**STEPS**:
1. Analyze `src/tools.py` to check the logic inside `check_return_eligibility`.
2. Verify the calculation of `days_since_delivery` and the comparison operators.
3. Identify the exact line causing the misclassification.
4. Propose a code patch to correct the logic (e.g., ensure it correctly flags 15 days as > 7 days or fix the boundary check).
5. Provide the complete corrected function or snippet.

**GUARDRAILS**:
- Do NOT modify the `MOCK_ORDERS` data.
- Do NOT change the tool function signature unless explicitly necessary.
- Ensure the fix is minimal and targeted.
```

---

## 🔧 Example of a Successful Agent Fix

*(Sau khi Agent phân tích và tìm thấy lỗi ở logic so sánh ngày)*

**Agent Output (Fixed Code)**:

```
✅ BUG FIXED

The issue was located in `src/tools.py`, specifically in the `check_return_eligibility` function.

**Root Cause**: The variable name `days_since_delivery` was correct, but the logic comparing it to the threshold was inverted.

**Code Patch**:

```python
    if days_since_delivery <= 7:
        return f"HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao {days_since_delivery} ngày trước (Thuộc hạn bảo hành đổi trả 7 ngày)."
    else:
        return f"KHÔNG HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao được {days_since_delivery} ngày (Quá thời hạn 7 ngày quy định)."
```

**Correction Applied**:

```python
    # Old: if days_since_delivery <= 7:
    # New: 
    if days_since_delivery < 7:
        return f"HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao {days_since_delivery} ngày trước (Thuộc hạn bảo hành đổi trả 7 ngày)."
    else:
        return f"KHÔNG HỢP LỆ ĐỔI TRẢ: Đơn hàng '{code}' đã giao được {days_since_delivery} ngày (Quá thời hạn 7 ngày quy định)."
```
*(Lưu ý: Agent có thể đề xuất thay đổi <= 7 thành < 7 hoặc logic đảo ngược hoàn toàn)*

**Verification Plan**:
Run the following test case:
```python
check_return_eligibility("ORD-1024") 
# Expected Output: "KHÔNG HỢP LỆ" (Since 15 > 7)
```
