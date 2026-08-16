# Kypzer AI Multi-Agent System

This directory contains the LangGraph and AutoGen integration for Kypzer AI, implementing an intelligent multi-agent system for voice command processing.

## Directory Structure

```
agents/
├── __init__.py                 # Package initialization and exports
├── base.py                     # Base classes for all agents
├── specialized/                # Domain-specific agent implementations
│   └── __init__.py
├── utils/                      # Shared utilities and helpers
│   ├── __init__.py
│   └── dependency_validator.py # Dependency checking utility
└── README.md                   # This file
```

## Installation

All required dependencies are listed in the root `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Key Dependencies

- **langgraph>=0.0.30**: Graph-based workflow orchestration
- **pyautogen>=0.2.0**: Multi-agent framework
- **langchain>=0.1.0**: LLM application framework
- **langchain-core>=0.1.0**: Core LangChain components
- **langchain-google-genai>=0.0.5**: Google Gemini integration

## Validation

To verify all dependencies are properly installed:

```bash
python -m agents.utils.dependency_validator
```

## Architecture

The agent system follows a graph-based orchestration pattern:

1. **Orchestrator Agent**: Central coordinator that routes commands
2. **StateGraph**: Manages workflow state and transitions
3. **Specialized Agents**: Domain-specific agents for different tasks
   - PC Control Agent
   - WhatsApp Agent
   - Screen AI Agent
   - Web Agent
   - Memory Agent

## Usage

(To be implemented in subsequent phases)

## Development Status

✅ **Phase 1 - Foundation** (Current)
- [x] Project structure created
- [x] Dependencies installed and verified
- [x] Base classes implemented

⬜ **Phase 2 - Agent Implementation** (Next)
- [ ] Specialized agent implementations
- [ ] State management
- [ ] Orchestration logic

## Contributing

This is part of the Kypzer AI project. See the main project documentation for contribution guidelines.
