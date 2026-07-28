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
    Trả về: (tools_used: list[str], steps: int) để so sánh với expected.
    """
    print(f"\n🤖 [REACT AGENT CẤP 3] Câu hỏi: {user_query}")

    conversation_history = f"Câu hỏi của người dùng: {user_query}\n"
    step = 0
    tools_used = []

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        llm_output = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"{llm_output.strip()}")

        if "Final Answer:" in llm_output:
            print("\n✅ AGENT ĐÃ HOÀN THÀNH NHIỆM VỤ. ---")
            return tools_used, step

        action_match = re.search(r"Action:\s*(.+)", llm_output)
        if action_match:
            action_cmd = action_match.group(1).strip()
            # Ghi nhận tên tool thực tế được gọi
            tool_name_match = re.search(r"(\w+)\[", action_cmd)
            if tool_name_match:
                tools_used.append(tool_name_match.group(1))

            obs = execute_tool_call(action_cmd)
            print(f"👁️ Observation: {obs}")
            conversation_history += f"\n{llm_output.strip()}\nObservation: {obs}\n"
        else:
            conversation_history += f"\n{llm_output.strip()}\n"

    print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
    print("🏁 Final Answer: Tôi đã kiểm tra thông tin trên hệ thống. Xin vui lòng liên hệ bộ phận hỗ trợ khách hàng để biết thêm thông tin chi tiết.")
    return tools_used, step


def print_test_header(tc: dict):
    """In thông tin expected của test case trước khi chạy agent."""
    sep = "=" * 65
    print(f"\n{sep}")
    print(f"📋 TEST {tc['id']}  |  {tc['category']}")
    print(sep)
    print(f"❓ Câu hỏi        : {tc['question']}")
    print(f"🎯 Expected Tools  : {tc.get('expected_tools', [])}")
    print(f"📏 Expected Steps  : {tc.get('expected_steps', '?')}")
    print(f"📌 Expected Behavior:\n   {tc.get('expected_behavior', '')}")
    if tc.get('guardrail_test'):
        print(f"🛡️  Guardrail Test  :\n   {tc['guardrail_test']}")
    print("-" * 65)


def print_comparison(tc: dict, tools_used: list, steps: int):
    """In bảng so sánh Expected vs Actual sau khi agent chạy xong."""
    sep = "-" * 65
    print(f"\n{sep}")
    print("📊 KẾT QUẢ SO SÁNH (Expected vs Actual):")
    print(sep)

    expected_tools = tc.get('expected_tools', [])
    expected_steps = tc.get('expected_steps', '?')

    # So sánh Tools
    if expected_tools:
        tools_match = all(t in tools_used for t in expected_tools)
        status_tools = "✅ KHỚP" if tools_match else "⚠️  KHÔNG KHỚP"
        print(f"  🛠️  Tools gọi thực tế : {tools_used if tools_used else ['(không có)']}")
        print(f"  🛠️  Tools mong đợi    : {expected_tools}")
        print(f"  Kết quả Tools        : {status_tools}")
    else:
        no_tool_ok = len(tools_used) == 0
        status_tools = "✅ KHỚP (không gọi tool)" if no_tool_ok else f"⚠️  Agent gọi tool không mong đợi: {tools_used}"
        print(f"  🛠️  Tools gọi thực tế : {tools_used if tools_used else ['(không có)']}")
        print(f"  🛠️  Tools mong đợi    : (không cần tool)")
        print(f"  Kết quả Tools        : {status_tools}")

    # So sánh Steps
    if isinstance(expected_steps, int):
        steps_ok = steps <= expected_steps + 1  # cho phép lệch 1 bước
        status_steps = "✅ KHỚP" if steps_ok else "⚠️  LỆCH"
        print(f"  📏 Số bước thực tế   : {steps}  |  Mong đợi: {expected_steps}  →  {status_steps}")
    else:
        print(f"  📏 Số bước thực tế   : {steps}")

    print(sep)


if __name__ == "__main__":
    print("=" * 65)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🛒 ĐỀ TÀI: TRỢ LÝ TRA CỨU ĐƠN HÀNG & XỬ LÝ ĐỔI TRẢ")
    print("=" * 65)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    # ----------------------------------------------------------------
    # Chọn test cases muốn chạy (mặc định: tất cả)
    # Để chạy riêng 1 test: selected = [tests[2]]
    # Để chạy nhiều test cụ thể: selected = [tests[0], tests[4], tests[7]]
    # ----------------------------------------------------------------
    selected = tests  # Chạy toàn bộ 8 test cases

    for i, tc in enumerate(selected):
        # --- In header expected ---
        print_test_header(tc)

        # --- Chạy ReAct Agent và thu kết quả thực tế ---
        tools_used, steps = run_react_agent(tc["question"], provider)

        # --- In bảng so sánh Expected vs Actual ---
        print_comparison(tc, tools_used, steps)

        if i < len(selected) - 1:
            input("\n⏸️  Nhấn Enter để chạy test tiếp theo...")

