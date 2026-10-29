# -*- coding: utf-8 -*-
"""
LLM客户端 —— 自然语言→SQL。
支持三种后端：
  1. OpenAI兼容API（OpenAI / DeepSeek / 智谱 / 通义 / vLLM 等）
  2. Ollama 本地大模型（OpenAI兼容协议 + 原生 /api/tags 模型扫描）
  3. Dify应用API
统一封装 nl2sql 调用，内置对推理型模型(<think>块)和markdown包裹的清理。
"""

import re
import requests
from typing import Optional, Tuple, List

import i18n


def list_ollama_models(base_url: str, timeout: int = 5) -> Tuple[List[str], str]:
    """
    扫描 Ollama 本地已下载模型列表。
    优先走原生 API GET {host}/api/tags（信息最全），失败回退 OpenAI 兼容 GET {base}/models。
    返回 (模型名列表, 错误信息)；服务不可用时返回 ([], 错误信息)。
    """
    base = (base_url or "").rstrip("/")
    if not base:
        return [], i18n.t("llm.scan_failed")

    # 1) Ollama 原生 API：base_url 形如 http://localhost:11434/v1 → host http://localhost:11434
    host = re.sub(r"/v1/?$", "", base)
    try:
        resp = requests.get(f"{host}/api/tags", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if models:
                return models, ""
    except Exception:
        pass

    # 2) OpenAI 兼容端点
    try:
        resp = requests.get(f"{base}/models", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            if models:
                return models, ""
        return [], i18n.t("llm.scan_failed")
    except requests.exceptions.ConnectionError:
        return [], i18n.t("llm.scan_failed")
    except Exception as e:
        return [], f"❌ {e}"


class LLMClient:
    """统一LLM客户端。"""

    def __init__(
        self,
        backend: str = "openai",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        dify_api_url: str = "https://api.dify.ai/v1",
        temperature: float = 0.0,
        timeout: int = 120,
    ):
        self.backend = backend
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or "").rstrip("/")
        self.model = (model or "").strip()
        self.dify_api_url = (dify_api_url or "").rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    def nl2sql(
        self,
        user_message: str,
        system_prompt: str,
        schema_hint: str,
        history: Optional[list] = None,
    ) -> str:
        """把自然语言转为SQL。返回SQL字符串；出错时以"❌ ..."开头。"""
        if self.backend == "dify":
            return self._call_dify(user_message, system_prompt, schema_hint, history or [])
        return self._call_openai_compatible(user_message, system_prompt, schema_hint, history or [])

    def test_connection(self) -> str:
        """测试LLM配置是否可用，返回 "" 表示成功，否则返回错误信息。"""
        try:
            if self.backend == "dify":
                url = f"{self.dify_api_url}/chat-messages"
                headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                payload = {
                    "inputs": {}, "query": "ping", "response_mode": "blocking",
                    "conversation_id": "", "user": "data-analyzer-test",
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=min(self.timeout, 30))
                if resp.status_code != 200:
                    return f"❌ Dify API错误 {resp.status_code}: {resp.text[:200]}"
                return ""
            url = f"{self.base_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 8,
                "stream": False,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=min(self.timeout, 30))
            if resp.status_code != 200:
                return f"❌ API错误 {resp.status_code}: {resp.text[:200]}"
            return ""
        except requests.exceptions.Timeout:
            return "❌ 连接超时，请检查网络或模型地址"
        except requests.exceptions.ConnectionError:
            return f"❌ 连接失败，请检查 Base URL 是否正确：{self.base_url}"
        except Exception as e:
            return f"❌ 测试失败: {e}"

    # ---------- OpenAI兼容协议 ----------
    def _call_openai_compatible(
        self,
        user_message: str,
        system_prompt: str,
        schema_hint: str,
        history: list,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = [{"role": "system", "content": system_prompt + "\n\n" + schema_hint}]
        for msg in history[-10:]:  # 最多带最近10轮，节省token
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False,
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return f"❌ API错误 {resp.status_code}: {resp.text[:300]}"
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return self._extract_sql(content)
        except requests.exceptions.Timeout:
            return "❌ 请求超时，请检查网络或模型地址"
        except requests.exceptions.ConnectionError:
            return f"❌ 连接失败，请检查 Base URL 是否正确：{self.base_url}"
        except Exception as e:
            return f"❌ 调用失败: {e}"

    # ---------- Dify协议 ----------
    def _call_dify(
        self,
        user_message: str,
        system_prompt: str,
        schema_hint: str,
        history: list,
    ) -> str:
        url = f"{self.dify_api_url}/chat-messages"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        full_query = (
            f"[系统提示词]\n{system_prompt}\n\n"
            f"[表结构信息]\n{schema_hint}\n\n"
            f"[用户需求]\n{user_message}"
        )
        payload = {
            "inputs": {},
            "query": full_query,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "data-analyzer-user",
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                return f"❌ Dify API错误 {resp.status_code}: {resp.text[:300]}"
            data = resp.json()
            answer = data.get("answer", "")
            return self._extract_sql(answer)
        except requests.exceptions.Timeout:
            return "❌ Dify请求超时"
        except requests.exceptions.ConnectionError:
            return f"❌ Dify连接失败，请检查URL：{self.dify_api_url}"
        except Exception as e:
            return f"❌ Dify调用失败: {e}"

    # ---------- 工具：从模型回复中提取SQL ----------
    @staticmethod
    def _extract_sql(text: str) -> str:
        """
        清理模型输出，提取纯SQL：
        1. 去掉推理型模型的 <think>...</think> 思考块
        2. 提取 ```sql ... ``` 代码块
        3. 从第一个 SELECT/WITH 关键字开始截取，去掉前后解释性文字
        """
        if not text:
            return ""
        # 1. 去思考块（贪婪匹配到最后一个闭合标签）
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = text.strip()

        # 2. 优先取 ```sql 代码块
        m = re.search(r"```(?:sql|sqlite)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if m:
            sql = m.group(1).strip()
        else:
            # 3. 从第一个 SELECT/WITH 开始
            m2 = re.search(r"\b(SELECT|WITH)\b", text, re.IGNORECASE)
            sql = text[m2.start():].strip() if m2 else text.strip()

        # 去掉首尾空白和结尾分号
        sql = sql.strip().rstrip(";").strip()
        return sql
