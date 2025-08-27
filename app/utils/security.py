import html
import re

def sanitize_input(input_string):
    """Sanitizar entrada de datos para prevenir XSS"""
    if not input_string:
        return input_string
    
    # Escapar caracteres HTML
    sanitized = html.escape(input_string)
    
    # Remover caracteres potencialmente peligrosos
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+=', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized

def sanitize_form_data(form_data):
    """Sanitizar todos los campos de un formulario"""
    sanitized_data = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            sanitized_data[key] = sanitize_input(value)
        else:
            sanitized_data[key] = value
    return sanitized_data