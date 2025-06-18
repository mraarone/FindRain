# ai/selector.py
from typing import Dict, List, Any, Optional, Type
from enum import Enum
import re

from .assistant import BaseAIAssistant, Message
from .models.claude import ClaudeAssistant
from .models.chatgpt import ChatGPTAssistant
from .models.gemini import GeminiAssistant

class QueryType(Enum):
    """Types of queries for model selection"""
    LONG_ANALYSIS = "long_analysis"
    QUICK_QUERY = "quick_query"
    WEB_SEARCH = "web_search"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SOCIAL_SENTIMENT = "social_sentiment"
    CODE_GENERATION = "code_generation"
    GENERAL = "general"

class ModelSelector:
    """Intelligent model selection based on query type"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, BaseAIAssistant] = {}
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize all configured AI models"""
        model_classes = {
            'claude': ClaudeAssistant,
            'chatgpt': ChatGPTAssistant,
            'gemini': GeminiAssistant,
            # 'grok': GrokAssistant  # Add when implemented
        }
        
        for model_name, model_config in self.config['AI_MODELS'].items():
            if model_config.get('api_key') and model_name in model_classes:
                try:
                    model_class = model_classes[model_name]
                    self.models[model_name] = model_class(
                        model_config['api_key'],
                        model_config
                    )
                    logger.info(f"Initialized {model_name} model")
                except Exception as e:
                    logger.error(f"Failed to initialize {model_name}: {e}")
    
    def classify_query(self, query: str) -> QueryType:
        """Classify the type of query"""
        query_lower = query.lower()
        
        # Pattern matching for query classification
        patterns = {
            QueryType.LONG_ANALYSIS: [
                r'analyze.*report',
                r'detailed.*analysis',
                r'comprehensive.*review',
                r'deep dive',
                r'write.*report'
            ],
            QueryType.WEB_SEARCH: [
                r'search.*web',
                r'latest.*news',
                r'current.*information',
                r'youtube',
                r'find.*online'
            ],
            QueryType.TECHNICAL_ANALYSIS: [
                r'technical.*analysis',
                r'chart.*pattern',
                r'indicator',
                r'moving average',
                r'rsi',
                r'macd'
            ],
            QueryType.SOCIAL_SENTIMENT: [
                r'social.*sentiment',
                r'twitter',
                r'reddit',
                r'what.*people.*saying',
                r'market.*sentiment'
            ],
            QueryType.CODE_GENERATION: [
                r'write.*code',
                r'create.*script',
                r'implement',
                r'build.*bot',
                r'trading.*algorithm'
            ],
            QueryType.QUICK_QUERY: [
                r'what is',
                r'quick',
                r'simple',
                r'brief'
            ]
        }
        
        for query_type, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, query_lower):
                    return query_type
        
        return QueryType.GENERAL
    
    def select_model(self, query: str, fallback: bool = True) -> Optional[BaseAIAssistant]:
        """Select the best model for the query"""
        query_type = self.classify_query(query)
        
        # Model preferences by query type
        model_preferences = {
            QueryType.LONG_ANALYSIS: ['claude', 'chatgpt', 'gemini'],
            QueryType.QUICK_QUERY: ['chatgpt', 'gemini', 'claude'],
            QueryType.WEB_SEARCH: ['gemini', 'grok', 'chatgpt'],
            QueryType.TECHNICAL_ANALYSIS: ['claude', 'chatgpt'],
            QueryType.SOCIAL_SENTIMENT: ['grok', 'gemini', 'chatgpt'],
            QueryType.CODE_GENERATION: ['claude', 'chatgpt'],
            QueryType.GENERAL: ['chatgpt', 'claude', 'gemini']
        }
        
        preferences = model_preferences.get(query_type, ['chatgpt', 'claude', 'gemini'])
        
        # Try models in order of preference
        for model_name in preferences:
            if model_name in self.models:
                model = self.models[model_name]
                if model.available:
                    logger.info(f"Selected {model_name} for {query_type.value} query")
                    return model
        
        # Fallback to any available model
        if fallback:
            for model_name, model in self.models.items():
                if model.available:
                    logger.warning(f"Using fallback model {model_name}")
                    return model
        
        logger.error("No available models found")
        return None
    
    def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all models"""
        status = {}
        for name, model in self.models.items():
            status[name] = {
                'available': model.available,
                'error_count': model.error_count,
                'success_count': model.success_count,
                'capabilities': model.get_capabilities()
            }
        return status


