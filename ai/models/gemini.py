# ai/models/gemini.py
import google.generativeai as genai
from typing import Dict, List, Any, Optional

from ..assistant import BaseAIAssistant, Message, AIResponse
from ...mcp.protocol import ToolDefinition

class GeminiAssistant(BaseAIAssistant):
    """Google Gemini assistant implementation"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__("Gemini", api_key, config)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.get('model', 'gemini-pro'))
        self.max_tokens = config.get('max_tokens', 4096)
        
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AIResponse:
        """Generate response using Gemini API"""
        try:
            # Convert messages to Gemini format
            chat = self.model.start_chat(history=[])
            
            for msg in messages[:-1]:  # Add history except last message
                if msg.role == 'user':
                    chat.send_message(msg.content)
                
            # Send the last user message
            response = await asyncio.to_thread(
                chat.send_message,
                messages[-1].content
            )
            
            self.record_success()
            
            return AIResponse(
                content=response.text,
                model=self.model.model_name,
                usage={
                    'total_tokens': len(response.text.split())  # Approximate
                },
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            self.record_error()
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Gemini's capabilities"""
        return {
            'strengths': [
                'web_search',
                'youtube_analysis',
                'multimodal',
                'real_time_data',
                'google_integration'
            ],
            'context_window': 1000000,  # 1M tokens for Gemini 1.5
            'supports_vision': True,
            'supports_tools': True,
            'best_for': 'web_and_media_analysis'
        }


