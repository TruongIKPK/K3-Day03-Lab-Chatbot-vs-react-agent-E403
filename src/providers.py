"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-4o-mini, etc. - Hỗ trợ gọi API trực tiếp qua HTTP requests)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenAI API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Hỗ trợ giả lập ReAct Tool Calling đầy đủ không cần API Key)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        import re
        text = prompt.lower()
        
        # Nếu đang ở vòng lặp thứ 2 (đã có kết quả Observation từ Tool Execution)
        if "observation:" in text:
            return "Thought: Tôi đã thu thập đầy đủ thông tin dữ liệu từ CSDL SQLite để kết luận.\nFinal Answer: Dưới đây là thông tin tra cứu chi tiết từ hệ thống dành cho bạn."

        # Tra cứu mã đơn hàng cụ thể (ORD-XXXX)
        order_match = re.search(r"ord-\d+", text)
        if order_match:
            code = order_match.group(0).upper()
            if "hủy" in text or "cancel" in text:
                return f"Thought: Khách hàng muốn hủy đơn hàng {code}. Kích hoạt tool cancel_order.\nAction: cancel_order['{code}', 'Yêu cầu hủy từ khách hàng']"
            elif any(kw in text for kw in ["đổi trả", "trả hàng", "tra hang", "doi tra", "ticket", "return", "hoàn tiền", "hoan tien"]):
                return f"Thought: Khách hàng yêu cầu tạo ticket đổi trả cho đơn {code}. Dùng tool check_return_eligibility kiểm tra điều kiện 7 ngày trước.\nAction: check_return_eligibility['{code}']"
            else:
                return f"Thought: Truy vấn chi tiết đơn hàng {code} và vận chuyển trong CSDL.\nAction: get_order_details['{code}']"

        if any(kw in text for kw in ["đơn hàng của tôi", "danh sách đơn", "các đơn hàng", "xem đơn hàng", "tất cả đơn hàng"]):
            return "Thought: Khách hàng yêu cầu xem danh sách tất cả đơn hàng. Gọi tool get_user_orders.\nAction: get_user_orders[1]"
            
        if any(kw in text for kw in ["sản phẩm", "mặt hàng", "tìm kiếm", "bán gì", "có gì"]):
            return "Thought: Khách hàng yêu cầu xem/tìm kiếm danh mục sản phẩm. Gọi tool search_products.\nAction: search_products['%']"
            
        if any(kw in text for kw in ["admin", "doanh thu", "báo cáo", "thống kê"]):
            return "Thought: Quản trị viên yêu cầu xem báo cáo tổng quan Admin. Gọi tool get_admin_dashboard_summary.\nAction: get_admin_dashboard_summary[3]"

        return "Thought: Tiếp nhận câu hỏi và chào hỏi người dùng.\nFinal Answer: 👋 Xin chào! Tôi là Trợ lý AI E-Commerce (ReAct Agent Cấp 3). Bạn cần tôi hỗ trợ tra cứu đơn hàng, vận chuyển hay đổi trả sản phẩm gì hôm nay?"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
