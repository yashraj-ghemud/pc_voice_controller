"""
Specialized agents for domain-specific tasks.

This package contains all specialized agent implementations:
- PCControlAgent: System control (volume, brightness, apps)
- WhatsAppAgent: WhatsApp messaging and file sharing
- ScreenAIAgent: Vision-based UI interaction
- WebAgent: Web search and browser automation
- MemoryAgent: Conversation memory and context retrieval
"""

from agents.specialized.pc_control_agent import PCControlAgent
from agents.specialized.memory_agent import MemoryAgent

__all__ = [
    "PCControlAgent",
    "MemoryAgent",
]
