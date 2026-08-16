"""
User-friendly error messages for the Kypzer AI agent system.

This module provides functions to convert technical errors into user-friendly
messages suitable for TTS output. Supports both Hindi and English.

Validates: Requirement 12.5
"""

from typing import Dict, Optional


# Error message templates in Hindi and English
ERROR_TEMPLATES = {
    # Network and connectivity errors
    "timeout": {
        "en": "The operation took too long to complete. Please try again.",
        "hi": "ऑपरेशन पूरा होने में बहुत समय लग गया। कृपया फिर से कोशिश करें।"
    },
    "network": {
        "en": "Network connection issue. Please check your internet connection.",
        "hi": "नेटवर्क कनेक्शन में समस्या है। कृपया अपना इंटरनेट कनेक्शन जांचें।"
    },
    "connection": {
        "en": "Unable to connect. Please check your connection and try again.",
        "hi": "कनेक्ट नहीं हो पा रहा है। कृपया अपना कनेक्शन जांचें और फिर से कोशिश करें।"
    },
    
    # Rate limiting
    "rate_limit": {
        "en": "Too many requests. Please wait a moment and try again.",
        "hi": "बहुत सारे रिक्वेस्ट हो गए हैं। कृपया थोड़ा इंतज़ार करें और फिर से कोशिश करें।"
    },
    "429": {
        "en": "Service is busy. Please wait a moment.",
        "hi": "सर्विस व्यस्त है। कृपया थोड़ा इंतज़ार करें।"
    },
    
    # Authorization and permission errors
    "unauthorized": {
        "en": "You don't have permission to perform this action.",
        "hi": "आपको यह एक्शन करने की अनुमति नहीं है।"
    },
    "forbidden": {
        "en": "This action is not allowed.",
        "hi": "यह एक्शन की अनुमति नहीं है।"
    },
    
    # Agent-specific errors
    "agent_not_found": {
        "en": "Could not find the right agent for this task.",
        "hi": "इस काम के लिए सही एजेंट नहीं मिला।"
    },
    "agent_failed": {
        "en": "The agent encountered an error. Please try again.",
        "hi": "एजेंट को एरर आ गई। कृपया फिर से कोशिश करें।"
    },
    
    # WhatsApp errors
    "whatsapp": {
        "en": "WhatsApp message could not be sent. Please check if WhatsApp is running.",
        "hi": "व्हाट्सएप मैसेज नहीं भेजा जा सका। कृपया चेक करें कि व्हाट्सएप चल रहा है या नहीं।"
    },
    "contact_not_found": {
        "en": "Contact not found. Please check the name and try again.",
        "hi": "कॉन्टैक्ट नहीं मिला। कृपया नाम चेक करें और फिर से कोशिश करें।"
    },
    "file_not_found": {
        "en": "File not found. Please check the file name.",
        "hi": "फाइल नहीं मिली। कृपया फाइल का नाम चेक करें।"
    },
    
    # Screen AI errors
    "element_not_found": {
        "en": "Could not find the element on screen. Please try again.",
        "hi": "स्क्रीन पर एलिमेंट नहीं मिला। कृपया फिर से कोशिश करें।"
    },
    "click_failed": {
        "en": "Could not click on the element. Please try again.",
        "hi": "एलिमेंट पर क्लिक नहीं हो सका। कृपया फिर से कोशिश करें।"
    },
    "type_failed": {
        "en": "Could not type in the field. Please try again.",
        "hi": "फील्ड में टाइप नहीं हो सका। कृपया फिर से कोशिश करें।"
    },
    
    # PC control errors
    "volume_failed": {
        "en": "Could not adjust volume. Please check your audio settings.",
        "hi": "वॉल्यूम एडजस्ट नहीं हो सका। कृपया अपनी ऑडियो सेटिंग्स चेक करें।"
    },
    "brightness_failed": {
        "en": "Could not adjust brightness. Please check your display settings.",
        "hi": "ब्राइटनेस एडजस्ट नहीं हो सकी। कृपया अपनी डिस्प्ले सेटिंग्स चेक करें।"
    },
    "app_not_found": {
        "en": "Could not find the application. Please check if it's installed.",
        "hi": "एप्लीकेशन नहीं मिली। कृपया चेक करें कि वह इंस्टॉल है या नहीं।"
    },
    
    # Web agent errors
    "search_failed": {
        "en": "Web search failed. Please check your browser.",
        "hi": "वेब सर्च फेल हो गई। कृपया अपना ब्राउज़र चेक करें।"
    },
    "url_invalid": {
        "en": "Invalid URL. Please check the address.",
        "hi": "गलत URL है। कृपया एड्रेस चेक करें।"
    },
    
    # Memory errors
    "memory_save_failed": {
        "en": "Could not save to memory. The conversation may not be remembered.",
        "hi": "मेमोरी में सेव नहीं हो सका। बातचीत याद नहीं रहेगी।"
    },
    "memory_retrieve_failed": {
        "en": "Could not retrieve past conversations.",
        "hi": "पुरानी बातचीत नहीं मिल सकी।"
    },
    
    # Generic fallback errors
    "unknown": {
        "en": "Something went wrong. Please try again.",
        "hi": "कुछ गलत हो गया। कृपया फिर से कोशिश करें।"
    },
    "invalid_input": {
        "en": "Invalid input. Please try again with a different command.",
        "hi": "गलत इनपुट। कृपया दूसरी कमांड से कोशिश करें।"
    },
    "max_retries": {
        "en": "Operation failed after multiple attempts. Please try a different approach.",
        "hi": "कई कोशिशों के बाद भी ऑपरेशन फेल हो गया। कृपया दूसरा तरीका अपनाएं।"
    }
}


def get_user_friendly_error(
    error_message: str,
    language: str = "hi",
    agent_name: Optional[str] = None
) -> str:
    """
    Convert technical error message to user-friendly TTS message.
    
    Analyzes the technical error message and returns an appropriate user-friendly
    message in the specified language (Hindi or English). Uses pattern matching
    to identify error types and map them to pre-defined templates.
    
    Args:
        error_message: Technical error message from agent execution
        language: Target language - "hi" for Hindi, "en" for English
        agent_name: Optional agent name for context-specific messages
        
    Returns:
        User-friendly error message in the specified language
        
    Validates: Requirement 12.5
    
    Examples:
        >>> get_user_friendly_error("timeout occurred", "en")
        'The operation took too long to complete. Please try again.'
        
        >>> get_user_friendly_error("network error", "hi")
        'नेटवर्क कनेक्शन में समस्या है। कृपया अपना इंटरनेट कनेक्शन जांचें।'
        
        >>> get_user_friendly_error("rate limit exceeded", "en")
        'Too many requests. Please wait a moment and try again.'
        
        >>> get_user_friendly_error("element not found", "hi", "screen_ai")
        'स्क्रीन पर एलिमेंट नहीं मिला। कृपया फिर से कोशिश करें।'
    """
    # Normalize language code
    language = language.lower()
    if language not in ["hi", "en"]:
        language = "hi"  # Default to Hindi
    
    # Convert error message to lowercase for matching
    error_lower = error_message.lower()
    
    # Try to match specific error patterns
    for error_key, messages in ERROR_TEMPLATES.items():
        if error_key in error_lower:
            return messages[language]
    
    # Agent-specific error handling
    if agent_name:
        agent_lower = agent_name.lower()
        
        # WhatsApp agent errors
        if "whatsapp" in agent_lower or "wa" in agent_lower:
            if "contact" in error_lower or "not found" in error_lower:
                return ERROR_TEMPLATES["contact_not_found"][language]
            elif "file" in error_lower:
                return ERROR_TEMPLATES["file_not_found"][language]
            else:
                return ERROR_TEMPLATES["whatsapp"][language]
        
        # Screen AI agent errors
        elif "screen" in agent_lower or "screen_ai" in agent_lower:
            if "element" in error_lower or "not found" in error_lower:
                return ERROR_TEMPLATES["element_not_found"][language]
            elif "click" in error_lower:
                return ERROR_TEMPLATES["click_failed"][language]
            elif "type" in error_lower:
                return ERROR_TEMPLATES["type_failed"][language]
        
        # PC control agent errors
        elif "pc_control" in agent_lower or "pc" in agent_lower:
            if "volume" in error_lower:
                return ERROR_TEMPLATES["volume_failed"][language]
            elif "brightness" in error_lower:
                return ERROR_TEMPLATES["brightness_failed"][language]
            elif "app" in error_lower or "application" in error_lower:
                return ERROR_TEMPLATES["app_not_found"][language]
        
        # Web agent errors
        elif "web" in agent_lower:
            if "search" in error_lower:
                return ERROR_TEMPLATES["search_failed"][language]
            elif "url" in error_lower:
                return ERROR_TEMPLATES["url_invalid"][language]
        
        # Memory agent errors
        elif "memory" in agent_lower:
            if "save" in error_lower:
                return ERROR_TEMPLATES["memory_save_failed"][language]
            elif "retrieve" in error_lower:
                return ERROR_TEMPLATES["memory_retrieve_failed"][language]
    
    # Check for max retries
    if "max" in error_lower and "retries" in error_lower:
        return ERROR_TEMPLATES["max_retries"][language]
    
    # Check for validation errors
    if "invalid" in error_lower or "validation" in error_lower:
        return ERROR_TEMPLATES["invalid_input"][language]
    
    # Default fallback
    return ERROR_TEMPLATES["unknown"][language]


def format_error_for_tts(
    error: str,
    language: str = "hi",
    agent_name: Optional[str] = None,
    include_suggestion: bool = True
) -> str:
    """
    Format error message for TTS with optional actionable suggestion.
    
    Wraps get_user_friendly_error and optionally adds a suggestion for what
    the user should do next. The suggestion is context-aware based on error type.
    
    Args:
        error: Technical error message
        language: "hi" for Hindi, "en" for English
        agent_name: Optional agent name for context
        include_suggestion: Whether to append actionable suggestion
        
    Returns:
        Formatted error message ready for TTS
        
    Examples:
        >>> format_error_for_tts("network error", "en", include_suggestion=True)
        'Network connection issue. Please check your internet connection.'
        
        >>> format_error_for_tts("unknown error", "hi", include_suggestion=False)
        'कुछ गलत हो गया। कृपया फिर से कोशिश करें।'
    """
    friendly_message = get_user_friendly_error(error, language, agent_name)
    
    # For now, templates already include suggestions
    # Future enhancement: Add more detailed suggestions
    return friendly_message


def get_success_message(
    action: str,
    language: str = "hi",
    details: Optional[Dict] = None
) -> str:
    """
    Generate user-friendly success message for completed actions.
    
    Args:
        action: Action that was performed (e.g., "volume_up", "send_message")
        language: "hi" for Hindi, "en" for English
        details: Optional dict with action-specific details
        
    Returns:
        User-friendly success message
        
    Examples:
        >>> get_success_message("volume_up", "en")
        'Volume increased'
        
        >>> get_success_message("send_message", "hi", {"contact": "papa"})
        'मैसेज भेज दिया गया'
    """
    # Success message templates
    success_templates = {
        "volume_up": {
            "en": "Volume increased",
            "hi": "वॉल्यूम बढ़ा दिया गया"
        },
        "volume_down": {
            "en": "Volume decreased",
            "hi": "वॉल्यूम कम कर दिया गया"
        },
        "brightness_up": {
            "en": "Brightness increased",
            "hi": "ब्राइटनेस बढ़ा दी गई"
        },
        "brightness_down": {
            "en": "Brightness decreased",
            "hi": "ब्राइटनेस कम कर दी गई"
        },
        "send_message": {
            "en": "Message sent",
            "hi": "मैसेज भेज दिया गया"
        },
        "open_app": {
            "en": "Application opened",
            "hi": "एप्लीकेशन खोल दी गई"
        },
        "search": {
            "en": "Search completed",
            "hi": "सर्च पूरा हो गया"
        },
        "click": {
            "en": "Clicked successfully",
            "hi": "क्लिक हो गया"
        },
        "default": {
            "en": "Task completed",
            "hi": "काम पूरा हो गया"
        }
    }
    
    # Normalize language
    language = language.lower()
    if language not in ["hi", "en"]:
        language = "hi"
    
    # Get template or default
    template = success_templates.get(action, success_templates["default"])
    message = template[language]
    
    # Add details if provided
    if details and "contact" in details:
        contact = details["contact"]
        if language == "hi":
            message = f"{contact} को {message}"
        else:
            message = f"{message} to {contact}"
    
    return message
