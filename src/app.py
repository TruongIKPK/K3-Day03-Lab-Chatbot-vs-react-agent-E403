"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
import re
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    AVAILABLE_TOOLS,
    get_order_details,
    get_shipping_status,
    check_return_eligibility,
    create_return_request,
    get_user_orders
)
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline Cấp 2) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE CẤP 2] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot Cấp 2 trả lời:\n{response}")


def execute_tool_call(action_str: str) -> str:
    """
    Hàm phân tích lệnh Action (VD: 'get_order_details[ORD-8899]' hoặc 'check_return_eligibility[ORD-8899]') và thực thi tool.
    """
    match = re.search(r"(\w+)\[(.*?)\]", action_str)
    if not match:
        return f"LỖI: Định dạng Action không đúng: {action_str}"
        
    tool_name, raw_args = match.group(1), match.group(2)
    if tool_name not in AVAILABLE_TOOLS:
        return f"LỖI: Tool '{tool_name}' không tồn tại trong Registry."
        
    args = [arg.strip().strip("'\"") for arg in raw_args.split(",") if arg.strip()]
    
    try:
        tool_func = AVAILABLE_TOOLS[tool_name]
        return tool_func(*args)
    except Exception as e:
        return f"LỖI TRUY VẤN TOOL ({tool_name}): {str(e)}"


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent Cấp 3 (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT CẤP 3] Câu hỏi: {user_query}")
    
    # Chuẩn bị lịch sử hội thoại ReAct
    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM sinh bước tiếp theo (Thought & Action)
        llm_output = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"{llm_output.strip()}")
        
        # Kiểm tra nếu Agent đã xuất kết quả Final Answer
        if "Final Answer:" in llm_output:
            print("\n✅ AGENT ĐÃ HOÀN THÀNH NHIỆM VỤ.")
            return
            
        # Trích xuất lệnh Action
        action_match = re.search(r"Action:\s*(.+)", llm_output)
        if action_match:
            action_cmd = action_match.group(1).strip()
            # Thực thi tool
            obs = execute_tool_call(action_cmd)
            print(f"👁️ Observation: {obs}")
            
            # Cập nhật lịch sử hội thoại cho vòng lặp tiếp theo
            conversation_history += f"\n{llm_output.strip()}\nObservation: {obs}\n"
        else:
            # Fallback nếu LLM sinh câu trả lời mà không có từ khóa Action/Final Answer
            conversation_history += f"\n{llm_output.strip()}\n"
            
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        print("🏁 Final Answer: Tôi đã kiểm tra thông tin trên hệ thống. Xin vui lòng liên hệ bộ phận hỗ trợ khách hàng để biết thêm thông tin chi tiết.")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🛒 ĐỀ TÀI: TRỢ LÝ TRA CỨU ĐƠN HÀNG & XỬ LÝ ĐỔI TRẢ")
    print("==================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Lấy câu test số 3 (Multi-step tra cứu đơn)
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE (CẤP 2) ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--------------------------------------------------")
    print("--- DEMO 2: CHẠY TRÊN REACT AGENT (CẤP 3) ---")
    run_react_agent(sample_query, provider)
