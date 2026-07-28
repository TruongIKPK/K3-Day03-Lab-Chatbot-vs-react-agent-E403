# 💻 CÔNG NGHỆ & MÔI TRƯỜNG THỰC THI (TECH STACK)

> Chi tiết ngăn xếp công nghệ và thư viện cho hệ thống ReAct Agent.

---

## 🛠️ 1. STACK CÔNG NGHỆ LÕI

- **Ngôn ngữ lập trình**: Python 3.10+
- **LLM Engine & Provider**: Multi-Provider Adapter (`Google Gemini Flash 3.6 / Pro`, `OpenAI GPT-4o-mini`, hoặc `Offline Mock Mode`).
- **Framework & Libraries**:
  - `google-genai` / `openai`: Thư viện SDK chính thức kết nối LLM.
  - `python-dotenv`: Quản lý biến môi trường an toàn từ `.env`.
  - `pydantic` (Optional): Validation schema cho tham số tool.
  - `sqlite3` / `SQLAlchemy`: Tương tác với cơ sở dữ liệu E-Commerce 11 bảng.

---

## ⚙️ 2. MÔI TRƯỜNG CHẠY & NGUYÊN TẮC VẬN HÀNH

- **Terminal Encoding**: `UTF-8` (Hỗ trợ hiển thị tiếng Việt có dấu và Emojis trên Windows PowerShell/CMD).
- **Zero Heavy Dependency**: Hệ thống tự dựng ReAct Loop tối giản, thuần khiết (Pure Python) giúp học viên nắm bản chất mà không phụ thuộc vào các framework cồng kềnh như LangChain / LlamaIndex.
