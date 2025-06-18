# mcp/validators.py
from typing import Any, Dict, List, Optional
import re
from datetime import datetime

class ValidationError(Exception):
    """Raised when parameter validation fails"""
    pass

class ParameterValidator:
    """Validates tool parameters"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate stock/crypto symbol"""
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
        
        symbol = symbol.upper().strip()
        
        # Basic symbol validation (alphanumeric with some special chars)
        if not re.match(r'^[A-Z0-9\-\.]{1,20}$', symbol):
            raise ValidationError(f"Invalid symbol format: {symbol}")
        
        return symbol
    
    @staticmethod
    def validate_date(date_input: Any) -> datetime:
        """Validate and parse date input"""
        if isinstance(date_input, datetime):
            return date_input
        
        if isinstance(date_input, str):
            # Try common date formats
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d',
                '%d/%m/%Y',
                '%d-%m-%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
            
            raise ValidationError(f"Invalid date format: {date_input}")
        
        raise ValidationError(f"Date must be string or datetime, got {type(date_input)}")
    
    @staticmethod
    def validate_interval(interval: str) -> str:
        """Validate time interval"""
        valid_intervals = ['1s', '1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M']
        
        if interval not in valid_intervals:
            raise ValidationError(
                f"Invalid interval: {interval}. Must be one of {valid_intervals}"
            )
        
        return interval
    
    @staticmethod
    def validate_number(value: Any, min_val: Optional[float] = None, 
                       max_val: Optional[float] = None) -> float:
        """Validate numeric value"""
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Value must be numeric, got {type(value)}")
        
        if min_val is not None and num < min_val:
            raise ValidationError(f"Value {num} is below minimum {min_val}")
        
        if max_val is not None and num > max_val:
            raise ValidationError(f"Value {num} is above maximum {max_val}")
        
        return num
    
    @staticmethod
    def validate_parameters(definition: ToolDefinition, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all parameters for a tool"""
        validated = {}
        
        for param_def in definition.parameters:
            param_name = param_def.name
            param_value = params.get(param_name, param_def.default)
            
            # Check required parameters
            if param_def.required and param_value is None:
                raise ValidationError(f"Required parameter missing: {param_name}")
            
            if param_value is not None:
                # Type validation
                if param_def.type == str:
                    if not isinstance(param_value, str):
                        raise ValidationError(
                            f"Parameter {param_name} must be string, got {type(param_value)}"
                        )
                elif param_def.type == int:
                    try:
                        param_value = int(param_value)
                    except (TypeError, ValueError):
                        raise ValidationError(
                            f"Parameter {param_name} must be integer"
                        )
                elif param_def.type == float:
                    param_value = ParameterValidator.validate_number(
                        param_value, param_def.min_value, param_def.max_value
                    )
                elif param_def.type == datetime:
                    param_value = ParameterValidator.validate_date(param_value)
                
                # Choice validation
                if param_def.choices and param_value not in param_def.choices:
                    raise ValidationError(
                        f"Parameter {param_name} must be one of {param_def.choices}"
                    )
            
            validated[param_name] = param_value
        
        return validated


