import html
import re

def sanitize_input(input_string, strict=True):
    """Sanitizar entrada de datos para prevenir XSS"""
    if not input_string or not isinstance(input_string, str):
        return input_string
    
    if strict:
        # Escapar caracteres HTML (modo estricto)
        sanitized = html.escape(input_string)
        
        # Remover caracteres potencialmente peligrosos
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'on\w+=', '', sanitized, flags=re.IGNORECASE)
    else:
        # Modo menos estricto, solo escapar HTML
        sanitized = html.escape(input_string)
    
    return sanitized

def sanitize_form_data(form_data, strict_fields=None):
    """Sanitizar campos de texto de un formulario, evitando campos numéricos"""
    sanitized_data = {}
    strict_fields = strict_fields or []  # Campos que requieren sanitización estricta
    
    for key, value in form_data.items():
        if isinstance(value, str):
            # Aplicar sanitización estricta solo a campos específicos
            strict_mode = key in strict_fields
            sanitized_data[key] = sanitize_input(value, strict=strict_mode)
        else:
            # Mantener valores no string sin cambios (números, booleanos, etc.)
            sanitized_data[key] = value
    
    return sanitized_data

def sanitize_html_content(html_content):
    """Sanitizar contenido HTML permitiendo etiquetas básicas seguras"""
    if not html_content:
        return html_content
    
    # Lista de etiquetas permitidas (personalizable)
    allowed_tags = {
        'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'div', 'span',
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    }
    
    # Escapar todo primero
    sanitized = html.escape(html_content)
    
    # Revertir las etiquetas permitidas
    for tag in allowed_tags:
        sanitized = sanitized.replace(f'&lt;{tag}&gt;', f'<{tag}>')
        sanitized = sanitized.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
    
    return sanitized