# -*- coding: utf-8 -*-
"""
设置持久化：所有配置保存在项目目录 settings.json（本地明文，仅本机使用）。
API Key / Token 等敏感信息也在此文件中，详见使用手册「安全说明」。

v3.2 起三个后端配置彻底分家（旧版共用 llm_base_url/llm_api_key/llm_model，
后端切换时曾互相污染，导致 Ollama 扫描请求了 OpenAI 地址）：
  openai: openai_base_url / openai_api_key / openai_model
  ollama: ollama_base_url / ollama_model
  dify:   dify_api_url / dify_api_key
"""

import json
import os
from typing import Any, Dict

import config

_DEFAULTS = {
    "language": "zh",
    "theme": "light",
    "window_geometry": "1280x800",
    # LLM 后端选择
    "llm_backend": "openai",
    # OpenAI 兼容
    "openai_base_url": config.LLM_PRESETS["openai"]["base_url"],
    "openai_api_key": "",
    "openai_model": config.LLM_PRESETS["openai"]["model"],
    # Ollama 本地
    "ollama_base_url": "http://localhost:11434/v1",
    "ollama_model": "qwen2.5",
    # Dify
    "dify_api_url": "https://api.dify.ai/v1",
    "dify_api_key": "",
    # 提示词
    "prompt_template": config.DEFAULT_TEMPLATE,
    "custom_rules": "",
    "system_prompt": "",          # 空=使用模板默认
    # 加载/分页
    "row_limit": config.DEFAULT_ROW_LIMIT,
    "page_size": config.DEFAULT_PAGE_SIZE,
    # SQL 片段 DIY 存储（10 个槽位）
    "sql_snippets": [{"name": "", "sql": ""} for _ in range(10)],
    # Databricks
    "db_host": "",
    "db_http_path": "",
    "db_token": "",
    "db_catalog": "hive_metastore",
    "db_schema": "default",
    "db_query": "SELECT * FROM your_table LIMIT 1000",
}


class Settings:
    """单例式设置访问器。"""

    def __init__(self, path: str = None):
        self.path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), config.SETTINGS_FILE)
        self._data: Dict[str, Any] = dict(_DEFAULTS)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    self._data.update(saved)
        except Exception:
            # 配置文件损坏时回退默认值，不影响启动
            pass
        self._migrate()

    def _migrate(self):
        """旧版本设置迁移（幂等，可反复执行）。"""
        # v2/v3.0：local 后端改名 ollama
        if self._data.get("llm_backend") == "local":
            self._data["llm_backend"] = "ollama"
        # v3.1 及以前：三个后端共用 llm_base_url/llm_api_key/llm_model，
        # 后端切换 bug 会把 OpenAI 配置写回去，污染 Ollama/Dify。这里按值自愈：
        old_base = str(self._data.get("llm_base_url", ""))
        old_key = str(self._data.get("llm_api_key", ""))
        old_model = str(self._data.get("llm_model", ""))
        is_openai_url = ("openai.com" in old_base or "deepseek" in old_base
                         or "bigmodel" in old_base or "dashscope" in old_base)
        # 1) 被污染的 OpenAI URL 恢复默认（它本就不该属于旧共享键的 ollama 值）
        if is_openai_url:
            self._data["llm_base_url"] = config.LLM_PRESETS["openai"]["base_url"]
            if old_base and not self._data.get("openai_base_url"):
                self._data["openai_base_url"] = old_base
        # 2) 旧共享键的值搬到你各自的独立键（仅当独立键还是出厂值时）
        if old_base and "11434" in old_base and self._data.get("ollama_base_url") == _DEFAULTS["ollama_base_url"]:
            self._data["ollama_base_url"] = old_base
        if old_key and not self._data.get("openai_api_key"):
            self._data["openai_api_key"] = old_key
        # 3) 模型名：旧共享值只在该值看起来属于对应后端时才搬，避免把 gpt-4o-mini 塞给 ollama
        if self._data.get("llm_backend") == "openai" and old_model and not self._data.get("openai_model"):
            if old_model != config.LLM_PRESETS["openai"]["model"]:
                self._data["openai_model"] = old_model
        # 4) dify url 迁移（旧版 dify_api_url 键名不变，无需处理）

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value

    def set_many(self, mapping: Dict[str, Any]):
        self._data.update(mapping)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)
