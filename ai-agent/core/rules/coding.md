# 📜 QUY TẮC MÃ NGUỒN (CODING RULES)

1. Mã nguồn Python viết mạch lạc, tuân thủ PEP8.
2. Mọi Tool trong `src/tools.py` PHẢI có Docstring chuẩn giải thích rõ tham số và giá trị trả về để LLM hiểu đúng cách sử dụng.
3. Không để chương trình crash do lỗi ngoại lệ DB hay API call; bắt `try...except` và trả về chuỗi thông báo lỗi.
