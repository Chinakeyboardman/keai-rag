#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM 服务
支持本地模型和 API 调用
"""

from typing import Optional, List, Dict, Any
from pathlib import Path

from config.settings import settings


class LLMService:
    """LLM 服务类"""
    
    def __init__(self):
        """初始化 LLM 服务"""
        self.model_type = settings.LLM_MODEL_TYPE
        self.model_name = settings.LLM_MODEL_NAME
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.top_p = settings.LLM_TOP_P
        
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        if self.model_type == "local":
            self._load_local_model()
        elif self.model_type == "api":
            self._setup_api_client()
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
    
    def _load_local_model(self):
        """加载本地模型"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = settings.get_llm_model_path()
            if not model_path or not model_path.exists():
                raise FileNotFoundError(f"模型路径不存在: {model_path}")
            
            print(f"📦 加载本地 LLM 模型: {model_path}")
            
            # 加载 tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True
            )
            
            # 加载模型
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            
            if device == "cpu":
                self.model = self.model.to(device)
            
            print(f"✅ LLM 模型加载成功 (设备: {device})")
            
        except Exception as e:
            raise RuntimeError(f"加载本地 LLM 模型失败: {e}")
    
    def _setup_api_client(self):
        """设置 API 客户端"""
        try:
            from openai import OpenAI
            
            self.model = OpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE
            )
            print(f"✅ LLM API 客户端设置成功")
            
        except Exception as e:
            raise RuntimeError(f"设置 LLM API 客户端失败: {e}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            生成的文本
        """
        if not prompt or not prompt.strip():
            raise ValueError("提示词不能为空")
        
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        if self.model_type == "local":
            return self._generate_with_local_model(prompt, system_prompt, temp, max_tok)
        else:
            return self._generate_with_api(prompt, system_prompt, temp, max_tok)
    
    def _generate_with_local_model(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """使用本地模型生成"""
        try:
            import torch
            
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 应用聊天模板
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
            # 生成
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=self.top_p,
                    do_sample=temperature > 0
                )
            
            # 解码
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            raise RuntimeError(f"本地模型生成失败: {e}")
    
    def _generate_with_api(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """使用 API 生成"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=self.top_p
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"API 生成失败: {e}")
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }


# 全局单例
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


if __name__ == "__main__":
    """测试 LLM 服务"""
    print("=" * 60)
    print("LLM 服务测试")
    print("=" * 60)
    print()
    
    try:
        # 创建服务
        service = get_llm_service()
        print(f"✅ 服务创建成功")
        print(f"   {service.get_model_info()}")
        print()
        
        # 测试生成
        print("📝 测试文本生成...")
        prompt = "请用一句话解释什么是人工智能。"
        response = service.generate(prompt)
        print(f"   提示词: {prompt}")
        print(f"   回复: {response}")
        print()
        
        print("✅ LLM 服务测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

