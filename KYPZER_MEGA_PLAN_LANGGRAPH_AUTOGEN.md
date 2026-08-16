# 🤖 KYPZER AI — AGENTIC UPGRADE IMPLEMENTATION PLAN
## LangGraph + AutoGen Full Integration Blueprint

> **PURPOSE OF THIS DOCUMENT**
> Yeh document ek complete implementation blueprint hai Kypzer AI ke current architecture mein
> LangGraph aur AutoGen ko integrate karne ke liye. Is document ko IDE ke AI assistant ko deke
> bolo "is plan ke hisaab se existing project mein changes karo" — woh khud saara kaam karega.
>
> **IMPORTANT INSTRUCTION FOR IDE AI:**
> - Existing files ko DELETE mat karna — sirf extend/wrap karna hai
> - Fast routes (intent.py, fast_browser_route, fast_whatsapp_route) TOUCH NAHI KARNE
> - actions.py ko directly call karna — rewrite nahi karna
> - Ek ek section sequentially implement karna — pehle foundation, phir agents

---

## 📋 TABLE OF CONTENTS

1. [Current Architecture Understanding](#1-current-architecture-understanding)
2. [What We Are Adding — Big Picture](#2-what-we-are-adding--big-picture)
3. [New File Structure After Upgrade](#3-new-file-structure-after-upgrade)
4. [Core Concepts — LangGraph in Kypzer](#4-core-concepts--langgraph-in-kypzer)
5. [Core Concepts — AutoGen in Kypzer](#5-core-concepts--autogen-in-kypzer)
6. [KypzerState — The Central Nervous System](#6-kypzerstate--the-central-nervous-system)
7. [LangGraph Node 1 — UnderstandNode](#7-langgraph-node-1--understandnode)
8. [LangGraph Node 2 — SeeScreenNode](#8-langgraph-node-2--seescreennode)
9. [LangGraph Node 3 — PlanNode](#9-langgraph-node-3--plannode)
10. [LangGraph Node 4 — ExecuteNode](#10-langgraph-node-4--executenode)
11. [LangGraph Node 5 — VerifyNode](#11-langgraph-node-5--verifynode)
12. [LangGraph Node 6 — RespondNode](#12-langgraph-node-6--respondnode)
13. [LangGraph Node 7 — ErrorRecoveryNode](#13-langgraph-node-7--errorrecoverynode)
14. [LangGraph Graph Assembly — Full Flow](#14-langgraph-graph-assembly--full-flow)
15. [AutoGen Agent 1 — OrchestratorAgent](#15-autogen-agent-1--orchestratoragent)
16. [AutoGen Agent 2 — VisionAgent](#16-autogen-agent-2--visionagent)
17. [AutoGen Agent 3 — ActionAgent](#17-autogen-agent-3--actionagent)
18. [AutoGen Agent 4 — WhatsAppAgent](#18-autogen-agent-4--whatsappagent)
19. [AutoGen Agent 5 — MemoryAgent](#19-autogen-agent-5--memoryagent)
20. [AutoGen GroupChat — Multi-Agent Coordination](#20-autogen-groupchat--multi-agent-coordination)
21. [LangGraph + AutoGen Bridge](#21-langgraph--autogen-bridge)
22. [New brain.py — Replacing Old Gemini Brain](#22-new-brainpy--replacing-old-gemini-brain)
23. [New screen_ai.py — Vision Node Wrapper](#23-new-screen_aipy--vision-node-wrapper)
24. [New memory.py — State-Aware Memory](#24-new-memorypy--state-aware-memory)
25. [main.py Changes — Minimal Touch](#25-mainpy-changes--minimal-touch)
26. [WhatsApp Module — Agent Wrapper](#26-whatsapp-module--agent-wrapper)
27. [Retry & Error Recovery Logic — Full Detail](#27-retry--error-recovery-logic--full-detail)
28. [State Persistence — Conversation Context](#28-state-persistence--conversation-context)
29. [Performance Optimization Plan](#29-performance-optimization-plan)
30. [Testing Each Component](#30-testing-each-component)
31. [Integration Order — Step by Step](#31-integration-order--step-by-step)
32. [Complete Data Flow — All Scenarios](#32-complete-data-flow--all-scenarios)
33. [New Dependencies — requirements.txt Update](#33-new-dependencies--requirementstxt-update)
34. [Configuration — New env.env Keys](#34-configuration--new-envenv-keys)
35. [What Each Old File Becomes](#35-what-each-old-file-becomes)

---

## 1. CURRENT ARCHITECTURE UNDERSTANDING

### 1.1 Abhi Kypzer Kaise Kaam Karta Hai

Kypzer abhi **linear pipeline** hai — ek ke baad ek step, koi feedback loop nahi:

```
Voice → STT → [Fast Route Check] → [Intent Check] → [Gemini Brain] → Actions → TTS
```

Yeh pipeline theek hai simple commands ke liye, lekin complex tasks mein fail hota hai kyunki:
- Koi **verification nahi** — action hua ya nahi, pata nahi
- Koi **retry nahi** — agar WhatsApp nahi khula, woh bas fail ho jaata hai silently
- **Brain aur Vision disconnected hain** — screen_ai.py alag kaam karta hai, brain.py alag
- **No state tracking** — ek command complete hone ke baad saari context khatam
- **No multi-step intelligence** — "YouTube pe jake search karo aur first result click karo" type commands nahi chalte

### 1.2 Current Files ka Role

| File | Current Role | Upgrade Mein Kya Hoga |
|------|-------------|----------------------|
| `main.py` | Entry point, fast routes, command loop | **MINIMAL CHANGE** — sirf brain call replace |
| `brain.py` | Gemini ko prompt bhejo, JSON wapas lo | **REPLACE** — LangGraph brain banega |
| `actions.py` | Saare PC automation actions | **TOUCH NAHI** — agents isko call karenge |
| `intent.py` | 50+ offline regex patterns | **TOUCH NAHI** — fast path rakhna hai |
| `screen_ai.py` | Vision AI — Llama 4 Scout via Groq | **WRAP** — LangGraph node mein |
| `memory.py` | ChromaDB conversation storage | **ENHANCE** — state-aware banega |
| `mic.py` | Audio recording | **TOUCH NAHI** |
| `stt.py` | Google STT | **TOUCH NAHI** |
| `tts.py` | Inworld AI TTS | **TOUCH NAHI** |
| `whatsapp_module/` | WhatsApp automation | **WRAP** — AutoGen agent mein |

### 1.3 Current Problems Jo Fix Honge

**Problem 1: Silent Failures**
```
Abhi: WhatsApp open karo → pyautogui click karta hai → kuch hoga ya nahi, koi check nahi
After: WhatsApp open karo → click → Vision AI verify karta hai → retry agar fail
```

**Problem 2: No Complex Planning**
```
Abhi: "Chrome mein youtube.com pe jao aur Arijit Singh search karo"
      → Gemini ek action deta hai → woh fail ya incomplete hota hai

After: Orchestrator Agent command todta hai → subagents execute karte hain →
       har step verify hota hai → next step tabhi shuru hota hai
```

**Problem 3: No Context Between Commands**
```
Abhi: "Chrome kholo" → done. Next command: "YouTube pe jao" → Chrome ka context nahi
After: State mein save hai ki Chrome khula tha → next command context-aware hoga
```

**Problem 4: No Error Recovery**
```
Abhi: Step 3 fail → crash ya wrong output
After: Step 3 fail → Error Recovery Node → diagnose → alternative try → retry
```

---

## 2. WHAT WE ARE ADDING — BIG PICTURE

### 2.1 New Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│              (Voice / Text — same as before, no change)             │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FAST PATH — UNCHANGED (intent.py + fast routes)        │
│   Volume/Brightness/WiFi/YouTube → Instant response, NO LangGraph  │
└──────────────────┬───────────────────────────────────────────────────┘
                   │ Only complex commands reach here
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATION LAYER                    │
│                         (new langgraph_brain.py)                    │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐           │
│  │Understand│→ │SeeScreen │→ │  Plan   │→ │ Execute  │           │
│  │  Node    │  │  Node    │  │  Node   │  │  Node    │           │
│  └──────────┘  └──────────┘  └─────────┘  └────┬─────┘           │
│                                                  │                  │
│                    ┌─────────────────────────────┘                  │
│                    ▼                                                 │
│             ┌────────────┐       ┌──────────────┐                  │
│             │ Verify Node│──────▶│ Respond Node │                  │
│             └────┬───────┘       └──────────────┘                  │
│                  │ if failed                                        │
│                  ▼                                                   │
│          ┌──────────────────┐                                       │
│          │ ErrorRecovery    │──── retry back to Plan Node          │
│          │ Node             │                                       │
│          └──────────────────┘                                       │
└──────────────────────┬──────────────────────────────────────────────┘
                        │ Each node calls
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTOGEN AGENT LAYER                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   Orchestrator Agent                         │   │
│  │   (Boss — LLM decides which agent kab kaam kare)            │   │
│  └────┬────────────────┬──────────────────┬────────────────────┘   │
│       │                │                  │                         │
│       ▼                ▼                  ▼                         │
│  ┌─────────┐     ┌──────────┐      ┌──────────┐  ┌────────────┐   │
│  │ Vision  │     │  Action  │      │ WhatsApp │  │  Memory    │   │
│  │  Agent  │     │  Agent   │      │  Agent   │  │  Agent     │   │
│  │(screen) │     │(pyautogui│      │(handler) │  │(chromadb)  │   │
│  └────┬────┘     └────┬─────┘      └────┬─────┘  └────┬───────┘   │
│       │               │                 │              │            │
│       ▼               ▼                 ▼              ▼            │
│  screen_ai.py    actions.py      whatsapp_module/  memory.py       │
│  (UNCHANGED)     (UNCHANGED)     (UNCHANGED)       (ENHANCED)      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Design Principles

**Principle 1: Backward Compatibility**
- Fast routes + offline intents BILKUL touch nahi karne
- Sirf complex commands (jo abhi brain.py jaate hain) LangGraph mein jaayenge
- main.py mein sirf ek function call replace hoga

**Principle 2: Wrap, Don't Rewrite**
- actions.py ko agents wrapper ke through call karenge
- screen_ai.py ko LangGraph node mein wrap karenge
- memory.py ko enhance karenge, delete nahi

**Principle 3: State-First Design**
- Har command ka poora state track hoga — KypzerState TypedDict
- State mein: command, screen context, action plan, execution results, retry count
- State memory.py mein persist hogi next command ke liye context

**Principle 4: Graceful Degradation**
- Agar LangGraph fail → old brain.py fallback
- Agar AutoGen fail → direct actions.py call
- Agar Vision AI fail → blind execution (as before)

---

## 3. NEW FILE STRUCTURE AFTER UPGRADE

```
kypzer/
│
├── CORE SYSTEM (mostly unchanged)
│   ├── main.py                    ← MINIMAL CHANGE — one function call replaced
│   ├── brain.py                   ← KEEP as fallback, add wrapper
│   ├── actions.py                 ← UNTOUCHED
│   ├── intent.py                  ← UNTOUCHED
│   ├── memory.py                  ← ENHANCED — state-aware methods added
│   │
├── VOICE I/O (untouched)
│   ├── mic.py                     ← UNTOUCHED
│   ├── stt.py                     ← UNTOUCHED
│   └── tts.py                     ← UNTOUCHED
│
├── AI & VISION (wrapped)
│   ├── screen_ai.py               ← UNTOUCHED — wrapped by LangGraph node
│   └── grabifier.py               ← UNTOUCHED
│
├── NEW — LANGGRAPH LAYER
│   ├── langgraph_brain.py         ← NEW MAIN FILE — replaces brain.py call
│   ├── kypzer_state.py            ← NEW — TypedDict state definition
│   └── nodes/
│       ├── __init__.py
│       ├── understand_node.py     ← NEW — command understanding
│       ├── see_screen_node.py     ← NEW — wraps screen_ai.py
│       ├── plan_node.py           ← NEW — action planning
│       ├── execute_node.py        ← NEW — wraps actions.py
│       ├── verify_node.py         ← NEW — verifies action success
│       ├── respond_node.py        ← NEW — wraps tts.py
│       └── error_recovery_node.py ← NEW — handles failures
│
├── NEW — AUTOGEN AGENT LAYER
│   └── agents/
│       ├── __init__.py
│       ├── orchestrator_agent.py  ← NEW — boss agent
│       ├── vision_agent.py        ← NEW — wraps screen_ai.py
│       ├── action_agent.py        ← NEW — wraps actions.py
│       ├── whatsapp_agent.py      ← NEW — wraps whatsapp_module
│       ├── memory_agent.py        ← NEW — wraps memory.py
│       └── group_chat.py          ← NEW — multi-agent coordination
│
├── NEW — BRIDGE
│   └── agent_bridge.py            ← NEW — LangGraph nodes call AutoGen agents
│
├── WHATSAPP MODULE (untouched)
│   └── whatsapp_module/           ← UNTOUCHED
│
└── CONFIGURATION (additions only)
    ├── env.env                    ← ADD new keys for LangGraph config
    └── requirements.txt           ← ADD langgraph, pyautogen packages
```

---

## 4. CORE CONCEPTS — LANGGRAPH IN KYPZER

### 4.1 LangGraph Kya Hai — Simple Explanation

LangGraph ek **state machine** hai jo LLM agents ke liye banaya gaya hai.

Normal code mein:
```
function A → function B → function C → done
```

LangGraph mein:
```
Node A → Node B → Node C
           ↑         ↓
           └── if failed, retry
```

Fark yeh hai ki LangGraph mein:
1. **State** — poori conversation ka ek shared object jisko har node read/write kar sakta hai
2. **Conditional Edges** — "agar X hua toh Node Y pe jao, warna Node Z pe jao"
3. **Loops** — ek node ke output ke basis pe wapas kisi purane node pe ja sakte hain
4. **Persistence** — state ko save kar sakte hain, next call mein continue kar sakte hain

### 4.2 LangGraph Ka Flow Kypzer Mein

```
COMMAND AAYA: "Chrome kholo aur gmail check karo"

Step 1: UnderstandNode
  Input: "Chrome kholo aur gmail check karo"
  Kaam: Gemini se samjho — yeh multi-step command hai
  Output: intent="OPEN_APP_THEN_NAVIGATE", steps=["open_chrome", "navigate_to_gmail"]
  State Update: state.intent, state.action_plan set ho gayi

Step 2: SeeScreenNode  
  Input: state.action_plan (pehla step = "open_chrome")
  Kaam: Screenshot lo, dekho kya screen pe hai
  Output: "Chrome nahi khula hua, desktop visible hai"
  State Update: state.screen_context = "desktop visible, chrome closed"

Step 3: PlanNode
  Input: state.intent + state.screen_context
  Kaam: Exact actions decide karo
  Output: ["OPEN_APP:chrome", "WAIT:2s", "OPEN_URL:gmail.com"]
  State Update: state.action_plan = detailed steps

Step 4: ExecuteNode
  Input: state.action_plan[0] = "OPEN_APP:chrome"
  Kaam: actions.open_app("chrome") call karo
  Output: "chrome opened"
  State Update: state.last_result = "success", state.current_step = 1

Step 5: VerifyNode
  Input: state.last_result, state.current_step
  Kaam: Screenshot lo, dekho Chrome khula kya
  Output: "Chrome window visible hai" → success
  State Update: state.verification_result = "confirmed"

Edge Decision: success → continue to next step (OPEN_URL:gmail.com)
               failure → ErrorRecoveryNode

Step 6: ExecuteNode (again for next action)
  "navigate_to_gmail" execute...

[loop continues until all steps done]

Step 7: RespondNode
  "Chrome khol diya aur Gmail check kar lo!"
  tts.speak_async(response)
```

### 4.3 Why LangGraph Over Simple Loop

Simple loop approach:
```python
for step in steps:
    execute(step)
    # koi verification nahi
    # koi context nahi
    # agar fail → crash
```

LangGraph approach:
```python
# Har node ko pata hai poori state
# Conditional routing — fail → retry → alternative
# State persist hoti hai
# Subgraphs possible — ek complex action apna khud ka graph hota hai
```

---

## 5. CORE CONCEPTS — AUTOGEN IN KYPZER

### 5.1 AutoGen Kya Hai — Simple Explanation

AutoGen ek **multi-agent framework** hai jahan:
- Multiple AI agents hote hain, har ek ka alag role
- Agents aapas mein **chat karte hain** task solve karne ke liye
- Ek **UserProxy** agent hota hai jo actual code/tools run karta hai
- **GroupChat** possible hai — multiple agents ek saath ek problem solve karein

### 5.2 AutoGen Ka Flow Kypzer Mein

```
COMPLEX COMMAND AAYA: "Screen pe jo error hai use samjho aur fix karo"

LangGraph PlanNode → AutoGen GroupChat ko call karta hai

AutoGen GroupChat:
  Orchestrator: "VisionAgent, screen dekho"
  VisionAgent:  [screen_ai.py call] → "Python error: ModuleNotFoundError numpy"
  Orchestrator: "ActionAgent, pip install numpy run karo"
  ActionAgent:  [actions.py call] → "Terminal khola, command run ki"
  VisionAgent:  [screen verify] → "Install successful"
  Orchestrator: "Task complete"

GroupChat result → LangGraph ExecuteNode ko wapas milta hai
```

### 5.3 AutoGen vs LangGraph — Kab Kaunsa

| Situation | Use LangGraph | Use AutoGen |
|-----------|--------------|-------------|
| Single action with verification | ✅ | ❌ |
| Multi-step flow with retry | ✅ | ❌ |
| Need multiple specialists | ❌ | ✅ |
| Complex decision making | ✅ | ✅ (inside node) |
| Screen understanding + action | ✅ (nodes) | ✅ (agents) |
| WhatsApp multi-step | ✅ | ✅ |

**Kypzer mein:**
- LangGraph = outer shell, flow control, state management
- AutoGen = inner intelligence, specialist agents jab needed

---

## 6. KYPZERSTATE — THE CENTRAL NERVOUS SYSTEM

### 6.1 State Kya Hai

State ek **shared dictionary** hai jo poore LangGraph graph mein flow karta hai.
Jaise ek person ke dimaag mein kaam karne ke dauran jo kuch yaad rehta hai — wahi state hai.

Har node yeh state **read** karta hai aur kuch fields **update** karta hai.

### 6.2 KypzerState Definition — File: `kypzer_state.py`

**IMPLEMENT THIS EXACTLY:**

```python
# kypzer_state.py
# Yeh file create karo — koi existing file se conflict nahi

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class KypzerState(TypedDict):
    # ═══════════════════════════════════════════
    # INPUT — Voice se aaya hua command
    # ═══════════════════════════════════════════
    
    raw_command: str
    # Exact jo user ne bola: "Chrome kholo aur gmail check karo"
    
    command_timestamp: str
    # ISO format: "2026-06-09T14:30:00"
    # Har command ke liye set karo: datetime.now().isoformat()
    
    # ═══════════════════════════════════════════
    # UNDERSTANDING — Command ka matlab
    # ═══════════════════════════════════════════
    
    intent: str
    # UnderstandNode set karta hai
    # Examples: "OPEN_APP", "WHATSAPP_FILE", "SCREEN_CLICK", "MULTI_STEP", "SYSTEM_CONTROL"
    
    intent_confidence: float
    # 0.0 to 1.0 — kitna confident hai UnderstandNode
    # 0.9+ = high confidence, directly plan karo
    # 0.5-0.9 = medium, screen dekho phir plan karo
    # <0.5 = low, user se poochho ya simple fallback
    
    is_multi_step: bool
    # True agar command mein multiple actions hain
    # "Chrome kholo aur gmail check karo" → True
    # "Volume badha" → False (but yeh fast route mein intercept ho jaayega)
    
    extracted_params: Dict[str, Any]
    # UnderstandNode extract karta hai:
    # {
    #   "app_name": "chrome",
    #   "url": "gmail.com",
    #   "contact": None,
    #   "file_keyword": None,
    #   "message": None,
    #   "search_query": None,
    #   "volume_level": None,
    #   "action_type": "open_app_then_navigate"
    # }
    
    # ═══════════════════════════════════════════
    # SCREEN CONTEXT — Screen pe kya hai abhi
    # ═══════════════════════════════════════════
    
    screen_context: str
    # SeeScreenNode set karta hai
    # Human-readable description: "Desktop visible, no open windows, taskbar at bottom"
    
    screen_screenshot_path: Optional[str]
    # Last screenshot ka path: "screenshot_20260609_143000.png"
    # Verify Node bhi screenshot leta hai comparison ke liye
    
    ui_elements_found: List[Dict[str, Any]]
    # SeeScreenNode detect karta hai:
    # [
    #   {"element": "chrome_icon", "x": 100, "y": 950, "confidence": 0.95},
    #   {"element": "taskbar", "x": 0, "y": 960, "confidence": 1.0}
    # ]
    
    screen_state_before: str
    # ExecuteNode se PEHLE ki screen state
    # VerifyNode compare karta hai: before vs after
    
    screen_state_after: str
    # ExecuteNode ke BAAD ki screen state
    
    # ═══════════════════════════════════════════
    # ACTION PLAN — Kya karna hai
    # ═══════════════════════════════════════════
    
    action_plan: List[Dict[str, Any]]
    # PlanNode set karta hai — ordered list of actions
    # [
    #   {"step": 1, "action": "OPEN_APP", "value": "chrome", "wait_after": 2.0},
    #   {"step": 2, "action": "OPEN_URL", "value": "gmail.com", "wait_after": 1.5},
    #   {"step": 3, "action": "VERIFY", "expected": "gmail visible"}
    # ]
    
    current_step_index: int
    # Abhi konsa step execute ho raha hai (0-indexed)
    # ExecuteNode har successful step ke baad increment karta hai
    
    total_steps: int
    # action_plan.length — PlanNode set karta hai
    
    # ═══════════════════════════════════════════
    # EXECUTION RESULTS — Kya hua
    # ═══════════════════════════════════════════
    
    last_action_result: str
    # "success" ya "failed" ya "partial"
    # ExecuteNode set karta hai har step ke baad
    
    last_action_output: str
    # Kya output aaya: "Chrome opened successfully" ya "App not found"
    
    all_step_results: List[Dict[str, Any]]
    # Har step ka detailed result:
    # [
    #   {"step": 1, "action": "OPEN_APP", "result": "success", "output": "Chrome opened"},
    #   {"step": 2, "action": "OPEN_URL", "result": "success", "output": "Gmail loaded"}
    # ]
    
    # ═══════════════════════════════════════════
    # VERIFICATION — Kaam hua kya
    # ═══════════════════════════════════════════
    
    verification_result: str
    # "confirmed" — screen pe expected change aaya
    # "failed" — screen same hai ya wrong state
    # "skipped" — simple action tha, verification zaroorat nahi
    # "timeout" — screenshot lena fail hua
    
    verification_details: str
    # "Chrome window found in screenshot at top of screen"
    # "Expected Gmail but got error page"
    
    # ═══════════════════════════════════════════
    # RETRY & ERROR — Recovery tracking
    # ═══════════════════════════════════════════
    
    retry_count: int
    # Kitni baar retry hua hai — 0 se shuru
    # Max retry limit: 3 (ErrorRecoveryNode check karta hai)
    
    max_retries: int
    # Default: 3
    # Simple actions ke liye: 1
    # Critical actions ke liye: 5
    
    error_history: List[Dict[str, Any]]
    # [
    #   {
    #     "step": 2, 
    #     "error": "Chrome not found",
    #     "attempted_fix": "searched in taskbar",
    #     "timestamp": "2026-06-09T14:30:05"
    #   }
    # ]
    
    current_error: str
    # Latest error message
    
    recovery_strategy: str
    # ErrorRecoveryNode decide karta hai:
    # "retry_same" — same action dobara try karo
    # "retry_alternative" — alternative approach try karo
    # "skip_step" — is step ko skip karo, aage badho
    # "abort" — poora task abort karo
    # "ask_user" — user se poochho kya karna hai
    
    # ═══════════════════════════════════════════
    # AUTOGEN MULTI-AGENT — Agent coordination
    # ═══════════════════════════════════════════
    
    needs_multi_agent: bool
    # True agar command itna complex hai ki multiple specialized agents chahiye
    # PlanNode decide karta hai: complex screen interaction → True
    
    agent_conversation: List[Dict[str, str]]
    # AutoGen GroupChat ki conversation history:
    # [
    #   {"agent": "Orchestrator", "message": "VisionAgent, screen dekho"},
    #   {"agent": "VisionAgent", "message": "Gmail open hai, compose button top-right mein"},
    #   {"agent": "ActionAgent", "message": "Compose button click kiya"}
    # ]
    
    assigned_agent: str
    # "VisionAgent" / "ActionAgent" / "WhatsAppAgent" / "MemoryAgent"
    # Simple single-agent tasks ke liye
    
    # ═══════════════════════════════════════════
    # MEMORY & CONTEXT — Past conversations
    # ═══════════════════════════════════════════
    
    memory_context: str
    # memory.py se retrieve: relevant past commands/context
    # "2 commands pehle: Chrome open tha. Last command: Spotify play kiya"
    
    session_commands: List[str]
    # Is session mein abhi tak kya kya commands aaye:
    # ["chrome kholo", "gmail check karo", "volume badha"]
    
    # ═══════════════════════════════════════════
    # RESPONSE — User ko kya bolna hai
    # ═══════════════════════════════════════════
    
    response_text: str
    # RespondNode set karta hai — TTS ke liye
    # "Chrome khol diya aur Gmail load ho raha hai!"
    
    response_language: str
    # "hindi" / "english" / "hinglish"
    # Intent + user preference se decide hota hai
    
    # ═══════════════════════════════════════════
    # FLOW CONTROL — Graph routing
    # ═══════════════════════════════════════════
    
    next_node: str
    # Conditional edge routing ke liye:
    # "see_screen" / "plan" / "execute" / "verify" / "respond" / "error_recovery"
    
    should_skip_vision: bool
    # True agar action simple hai aur screen dekhe bina kaam chale
    # Example: "Volume 50 karo" → skip vision
    # Example: "Screen pe red button click karo" → don't skip
    
    is_complete: bool
    # True agar poori task complete ho gayi
    # RespondNode set karta hai True
    
    # ═══════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════
    
    session_id: str
    # Unique ID for this command session: "kypzer_20260609_143000_abc123"
    
    total_execution_time_ms: int
    # Poore command ka total time milliseconds mein
```

### 6.3 State Initialization — Har Command Ke Shuruat Mein

```python
def create_initial_state(command: str) -> KypzerState:
    """
    Yeh function main.py se call hoga jab bhi koi complex command aaye.
    Fast routes aur offline intents pehle filter kar lo — jo bacha woh yahan aayega.
    """
    import uuid
    from datetime import datetime
    
    return KypzerState(
        # Input
        raw_command=command,
        command_timestamp=datetime.now().isoformat(),
        
        # Understanding (blank — UnderstandNode fill karega)
        intent="",
        intent_confidence=0.0,
        is_multi_step=False,
        extracted_params={},
        
        # Screen (blank — SeeScreenNode fill karega)
        screen_context="",
        screen_screenshot_path=None,
        ui_elements_found=[],
        screen_state_before="",
        screen_state_after="",
        
        # Action Plan (blank — PlanNode fill karega)
        action_plan=[],
        current_step_index=0,
        total_steps=0,
        
        # Execution (blank)
        last_action_result="",
        last_action_output="",
        all_step_results=[],
        
        # Verification (blank)
        verification_result="",
        verification_details="",
        
        # Retry
        retry_count=0,
        max_retries=3,
        error_history=[],
        current_error="",
        recovery_strategy="",
        
        # AutoGen
        needs_multi_agent=False,
        agent_conversation=[],
        assigned_agent="",
        
        # Memory
        memory_context="",
        session_commands=[],
        
        # Response
        response_text="",
        response_language="hinglish",
        
        # Flow Control
        next_node="understand",
        should_skip_vision=False,
        is_complete=False,
        
        # Metadata
        session_id=f"kypzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        total_execution_time_ms=0,
    )
```

---

## 7. LANGGRAPH NODE 1 — UNDERSTANDNODE

### 7.1 Purpose

UnderstandNode ka kaam hai raw voice command ko **structured intent + params mein convert karna**.

Yeh node Gemini ko call karta hai (teri existing brain.py ki tarah, but more structured).

### 7.2 File: `nodes/understand_node.py`

**Logic in detail:**

```
INPUT: state.raw_command = "Papa ko resume bhejo WhatsApp pe"

PROCESS:
1. memory.py se relevant context lo (kya pehle WhatsApp use hua)
2. Gemini ko structured prompt bhejo:
   - Command kya hai
   - Past context kya hai
   - Possible intents ki list (OPEN_APP, WHATSAPP_MSG, WHATSAPP_FILE, etc.)
   - JSON format mein wapas do
3. Response parse karo → intent, params, confidence

OUTPUT: state updates:
  intent = "WHATSAPP_FILE_SMART"
  intent_confidence = 0.95
  is_multi_step = False  (single task hai)
  extracted_params = {
    "contact": "papa",
    "file_keyword": "resume",
    "send_type": "file"
  }
  should_skip_vision = False  (WhatsApp kholna padega)
```

**Gemini Prompt Template UnderstandNode ke liye:**

```
You are Kypzer AI's command understanding module.
Analyze the user's voice command and return ONLY valid JSON.

User Command: {raw_command}

Session Context (last 3 commands): {memory_context}

Classify the command into ONE of these intents:
- OPEN_APP: Open an application
- CLOSE_APP: Close an application  
- OPEN_URL: Navigate to a website
- SYSTEM_CONTROL: Volume/brightness/wifi/bluetooth
- WHATSAPP_TEXT: Send WhatsApp text message
- WHATSAPP_VOICE: Send WhatsApp voice note
- WHATSAPP_FILE: Send WhatsApp file
- SCREEN_CLICK: Click something on screen
- SCREEN_TYPE: Type something on screen
- SCREEN_READ: Read/analyze what's on screen
- MEDIA_CONTROL: Play/pause/next/prev
- POWER: Shutdown/restart/sleep/lock
- MULTI_STEP: Multiple sequential actions needed
- FLOW_ASMR: ASMR video generation
- GENERAL_QUERY: General question/conversation

Return ONLY this JSON structure:
{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "is_multi_step": false,
  "extracted_params": {
    "contact": null,
    "file_keyword": null,
    "app_name": null,
    "url": null,
    "message": null,
    "search_query": null,
    "click_target": null,
    "type_text": null,
    "volume_level": null,
    "brightness_level": null
  },
  "should_skip_vision": true,
  "response_language": "hinglish",
  "reasoning": "brief explanation"
}
```

**Decision Logic After Gemini Response:**

```
IF intent_confidence >= 0.9:
    → Directly to PlanNode (skip screen check for simple things)
    → BUT agar intent involves screen interaction → SeeScreenNode

IF intent_confidence >= 0.5 AND < 0.9:
    → SeeScreenNode pehle (context se confidence badhega)

IF intent_confidence < 0.5:
    → response_text = "Samjha nahi, please dobara bolo"
    → RespondNode direct

SPECIAL CASES:
- "should_skip_vision" = True → SYSTEM_CONTROL, MEDIA, POWER type actions
- "should_skip_vision" = False → SCREEN_CLICK, SCREEN_TYPE, WHATSAPP_*, OPEN_APP
```

### 7.3 State Updates by UnderstandNode

```python
state["intent"] = gemini_response["intent"]
state["intent_confidence"] = gemini_response["confidence"]
state["is_multi_step"] = gemini_response["is_multi_step"]
state["extracted_params"] = gemini_response["extracted_params"]
state["should_skip_vision"] = gemini_response["should_skip_vision"]
state["response_language"] = gemini_response["response_language"]
state["memory_context"] = memory.get_relevant_context(state["raw_command"])
```

---

## 8. LANGGRAPH NODE 2 — SEESCREENNODE

### 8.1 Purpose

SeeScreenNode ka kaam hai **current screen state samajhna** taaki PlanNode accurate decisions le sake.

Yeh node screen_ai.py ko call karta hai — **without modification**.

### 8.2 Logic Flow

```
INPUT: state.intent, state.extracted_params

DECISION: Kya screenshot lena zaroorat hai?
  - should_skip_vision = True → immediately PlanNode pe jao, state.screen_context = "SKIPPED"
  - SYSTEM_CONTROL/MEDIA/POWER → skip (screen dekhne ki zaroorat nahi)
  - OPEN_APP/WHATSAPP/SCREEN_* → screenshot lo

PROCESS (when needed):
1. mss se screenshot lo → save as "screenshot_{session_id}_before.png"
2. state.screen_state_before = screenshot_path
3. screen_ai.py ki analyze_screen() function call karo
4. Prompt: "Describe what's visible on screen. List all visible windows, buttons, icons. 
           The user wants to: {intent} with params: {extracted_params}. 
           What relevant UI elements are visible?"
5. Response parse karo → screen_context, ui_elements_found

OUTPUT state updates:
  screen_context = "Desktop visible, Chrome icon in taskbar, no windows open"
  screen_screenshot_path = "screenshot_xyz_before.png"
  ui_elements_found = [
    {"element": "chrome_taskbar", "x": 1200, "y": 960, "type": "icon"}
  ]
  screen_state_before = screen_context
```

### 8.3 screen_ai.py Integration Points

Existing `screen_ai.py` mein yeh functions use karne hain:
- `take_screenshot()` — ya direct mss use karo
- `analyze_screen(prompt)` — screenshot + prompt → LLM response
- `find_element(description)` → `{x, y, found: bool}`

**Agar screen_ai.py mein `analyze_screen(prompt)` nahi hai, toh yeh helper add karo:**

```python
# nodes/see_screen_node.py mein — screen_ai.py ko touch nahi karna
def get_screen_context(intent: str, params: dict) -> tuple[str, list]:
    """
    screen_ai.py ke existing functions use karo.
    Directly apni screenshot + Groq call karo agar needed.
    """
    import mss
    import base64
    from groq import Groq
    
    # Screenshot lo (screen_ai.py ki tarah)
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
        # PIL Image convert
        from PIL import Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        # Resize agar bada hai (screen_ai.py ka logic follow karo)
        if img.width > 1366:
            ratio = 1366 / img.width
            img = img.resize((1366, int(img.height * ratio)))
        
        # Base64 encode
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Groq Vision call
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": f"""
                    Describe the current screen state for a PC automation system.
                    
                    User's intended action: {intent}
                    Action parameters: {params}
                    
                    Return JSON:
                    {{
                      "screen_description": "brief description",
                      "relevant_elements": [
                        {{"element": "name", "x": 100, "y": 200, "type": "button/icon/window/text"}}
                      ],
                      "is_target_visible": true/false,
                      "blocker": "anything blocking the action or null"
                    }}
                """}
            ]
        }],
        max_tokens=500
    )
    
    # Parse response
    import json
    result = json.loads(response.choices[0].message.content)
    return result["screen_description"], result["relevant_elements"]
```

### 8.4 When to Skip SeeScreen

```
SKIP (should_skip_vision = True):
  - SYSTEM_CONTROL (volume, brightness, wifi, bluetooth, power)
  - MEDIA_CONTROL (play, pause, next, prev)
  - POWER (shutdown, restart, sleep, lock)
  - Simple OPEN_URL (just webbrowser.open, no interaction)

DON'T SKIP (need screen):
  - OPEN_APP (verify it opened)
  - SCREEN_CLICK (need coordinates)
  - SCREEN_TYPE (need to find input field)
  - WHATSAPP_* (need to see WhatsApp state)
  - FLOW_ASMR (need to see Flow app state)
  - MULTI_STEP (complex — always check screen)
```

---

## 9. LANGGRAPH NODE 3 — PLANNODE

### 9.1 Purpose

PlanNode ka kaam hai **exact step-by-step action plan banana** jo ExecuteNode execute karega.

Yeh node sabse intelligent node hai — yahan pe decide hota hai ki AutoGen agents chahiye ya nahi.

### 9.2 Logic Flow

```
INPUT: 
  state.intent = "WHATSAPP_FILE_SMART"
  state.extracted_params = {contact: "papa", file_keyword: "resume"}
  state.screen_context = "Desktop visible, WhatsApp not open"
  state.memory_context = "Last command: opened chrome"

PROCESS:
1. Check: is_multi_step ya complex intent?
   - "WHATSAPP_FILE_SMART" → complex, multi-step
   - state.needs_multi_agent = True

2. Generate action_plan:
   Gemini ya rule-based logic se:
   [
     {step: 1, action: "SEARCH_FILES", value: "resume", wait_after: 0},
     {step: 2, action: "SPEAK_OPTIONS", value: "files found list", wait_after: 3},
     {step: 3, action: "LISTEN_SELECTION", value: "voice select", wait_after: 0},
     {step: 4, action: "COPY_FILE", value: "selected_file", wait_after: 0},
     {step: 5, action: "OPEN_WHATSAPP", value: "papa", wait_after: 3},
     {step: 6, action: "PASTE_AND_SEND", value: null, wait_after: 1},
     {step: 7, action: "VERIFY_SENT", value: null, wait_after: 0}
   ]

3. total_steps = 7
4. current_step_index = 0

OUTPUT state updates:
  action_plan = [list above]
  total_steps = 7
  current_step_index = 0
  needs_multi_agent = True  (complex WhatsApp operation)
```

### 9.3 Rule-Based Plans for Common Intents

Yeh predefined plans hain jo Gemini call ki zaroorat nahi — directly set karo:

**OPEN_APP plan:**
```python
[
  {"step": 1, "action": "OPEN_APP", "value": params["app_name"], "wait_after": 2.0},
  {"step": 2, "action": "VERIFY_APP_OPEN", "value": params["app_name"], "wait_after": 0}
]
```

**OPEN_URL plan:**
```python
[
  {"step": 1, "action": "OPEN_URL", "value": params["url"], "wait_after": 1.5}
]
```

**WHATSAPP_TEXT plan:**
```python
[
  {"step": 1, "action": "OPEN_WHATSAPP_CHAT", "value": params["contact"], "wait_after": 2.0},
  {"step": 2, "action": "TYPE_MESSAGE", "value": params["message"], "wait_after": 0.5},
  {"step": 3, "action": "SEND_MESSAGE", "value": None, "wait_after": 1.0},
  {"step": 4, "action": "VERIFY_SENT", "value": None, "wait_after": 0}
]
```

**WHATSAPP_FILE plan:**
```python
[
  {"step": 1, "action": "SEARCH_FILES", "value": params["file_keyword"], "wait_after": 0},
  {"step": 2, "action": "PRESENT_FILE_OPTIONS", "value": None, "wait_after": 4.0},
  {"step": 3, "action": "LISTEN_VOICE_SELECT", "value": None, "wait_after": 0},
  {"step": 4, "action": "COPY_SELECTED_FILE", "value": None, "wait_after": 0},
  {"step": 5, "action": "OPEN_WHATSAPP_CHAT", "value": params["contact"], "wait_after": 2.5},
  {"step": 6, "action": "PASTE_AND_SEND", "value": None, "wait_after": 1.0},
  {"step": 7, "action": "VERIFY_SENT", "value": None, "wait_after": 0}
]
```

**SCREEN_CLICK plan:**
```python
[
  {"step": 1, "action": "FIND_AND_CLICK", "value": params["click_target"], "wait_after": 0.5}
  # screen_ai.py automatically coordinates dhundega
]
```

**MULTI_STEP (use Gemini to generate plan):**
```python
# Gemini ko complete prompt bhejo:
# "Generate an action plan for: {raw_command}
#  Screen context: {screen_context}
#  Available actions: OPEN_APP, OPEN_URL, TYPE_TEXT, PRESS_KEY, CLICK_AT,
#                     FIND_AND_CLICK, SCROLL_DOWN, SCREENSHOT, WAIT
#  Return JSON array of steps."
```

### 9.4 needs_multi_agent Decision

```python
def should_use_multi_agent(intent: str, action_plan: list) -> bool:
    """
    Decide karo AutoGen GroupChat chahiye ya single agent kaafi hai
    """
    complex_intents = [
        "WHATSAPP_FILE_SMART",   # File search + WhatsApp combo
        "FLOW_ASMR",             # Complex 15-step automation
        "MULTI_STEP",            # Multiple app interactions
        "SCREEN_DEBUG",          # Error reading + fixing
    ]
    
    # Agar plan mein 5+ steps hain
    if len(action_plan) >= 5:
        return True
    
    # Agar complex intent hai
    if intent in complex_intents:
        return True
    
    # Agar plan mein VERIFY step hai AND complex action before
    has_verify = any(s["action"].startswith("VERIFY") for s in action_plan)
    has_complex = any(s["action"] in ["SEARCH_FILES", "FIND_AND_CLICK"] for s in action_plan)
    if has_verify and has_complex:
        return True
    
    return False
```

---

## 10. LANGGRAPH NODE 4 — EXECUTENODE

### 10.1 Purpose

ExecuteNode ka kaam hai **action_plan ka current step actually execute karna**.

Yeh node `actions.py` ko call karta hai — **without modification**.
Complex cases mein AutoGen agents ko delegate karta hai.

### 10.2 Simple Execution — Direct actions.py Call

Yeh mapping hai action names se `actions.py` functions tak:

```python
# nodes/execute_node.py

import sys
sys.path.append("..")  # parent directory mein actions.py hai
import actions  # tera existing actions.py

ACTION_MAP = {
    "OPEN_APP": lambda val, params: actions.open_app(val),
    "CLOSE_APP": lambda val, params: actions.close_app(val),
    "OPEN_URL": lambda val, params: actions.open_url(val),
    "VOLUME_UP": lambda val, params: actions.change_volume(+10),
    "VOLUME_DOWN": lambda val, params: actions.change_volume(-10),
    "VOLUME_SET": lambda val, params: actions.set_volume(int(val)),
    "BRIGHTNESS_UP": lambda val, params: actions.change_brightness(+10),
    "BRIGHTNESS_DOWN": lambda val, params: actions.change_brightness(-10),
    "TYPE_TEXT": lambda val, params: actions.type_text(val),
    "PRESS_KEY": lambda val, params: actions.press_key(val),
    "SCREENSHOT": lambda val, params: actions.take_screenshot(),
    "OPEN_WHATSAPP_CHAT": lambda val, params: actions.execute_steps([
        {"action": "SEND_WHATSAPP_MESSAGE", "value": val}
    ]),
    # ... baaki actions.py functions map karo
}

def execute_current_step(state: KypzerState) -> KypzerState:
    current_step = state["action_plan"][state["current_step_index"]]
    action = current_step["action"]
    value = current_step.get("value")
    
    try:
        if action in ACTION_MAP:
            result = ACTION_MAP[action](value, state["extracted_params"])
            state["last_action_result"] = "success"
            state["last_action_output"] = str(result)
        else:
            # Unknown action — screen_ai.py se try karo
            result = try_vision_action(action, value, state)
            
    except Exception as e:
        state["last_action_result"] = "failed"
        state["last_action_output"] = str(e)
        state["current_error"] = str(e)
    
    # Step result record karo
    state["all_step_results"].append({
        "step": current_step["step"],
        "action": action,
        "result": state["last_action_result"],
        "output": state["last_action_output"]
    })
    
    # Wait if specified
    if current_step.get("wait_after", 0) > 0:
        import time
        time.sleep(current_step["wait_after"])
    
    return state
```

### 10.3 Complex Execution — AutoGen Delegation

```
TRIGGER: state.needs_multi_agent = True

PROCESS:
1. agent_bridge.py ko call karo
2. Relevant agents ko task pass karo
3. GroupChat conversation record karo state mein
4. Final result wapas lo

Example — WHATSAPP_FILE complex execution:

agent_bridge.execute_with_agents(
    task="Send resume file to papa on WhatsApp",
    agents=["WhatsAppAgent"],  # ya multiple agar needed
    context=state
)

WhatsAppAgent internally calls:
  → whatsapp_module/handler.py (unchanged)
  → whatsapp_module/wa_controller.py (unchanged)
  → whatsapp_module/file_search.py (unchanged)
```

### 10.4 Special Action Handlers

**FIND_AND_CLICK — screen_ai.py use karo:**
```python
def handle_find_and_click(target: str, state: KypzerState) -> str:
    """
    screen_ai.py se element dhundo aur click karo.
    screen_ai.py ka find_and_click() function agar exist karta hai use karo.
    Warna khud implement karo using screen_ai.py ka screenshot + Groq call.
    """
    # Existing screen_ai.py function call:
    # screen_ai.click_element(target)
    
    # Ya agar woh function nahi:
    import screen_ai
    result = screen_ai.find_element(target)  # existing function
    if result and result.get("found"):
        import pyautogui
        pyautogui.click(result["x"], result["y"])
        return f"Clicked {target} at ({result['x']}, {result['y']})"
    else:
        raise Exception(f"Element '{target}' not found on screen")
```

**VERIFY_APP_OPEN:**
```python
def handle_verify_app_open(app_name: str) -> str:
    import pygetwindow as gw
    windows = gw.getWindowsWithTitle(app_name)
    if windows:
        return "verified"
    else:
        raise Exception(f"App '{app_name}' window not found after opening")
```

**VERIFY_SENT (WhatsApp):**
```python
def handle_verify_sent() -> str:
    # Screenshot lo aur check karo "tick" visible hai kya
    import screen_ai
    context = screen_ai.analyze_screen(
        "Is there a sent message visible (blue double tick or single tick) in WhatsApp?"
    )
    if "tick" in context.lower() or "sent" in context.lower():
        return "verified"
    raise Exception("Message sent verification failed")
```

---

## 11. LANGGRAPH NODE 5 — VERIFYNODE

### 11.1 Purpose

VerifyNode ka kaam hai **check karna ki last executed action actually hua ya nahi**.

Yeh node screen ka "before" aur "after" state compare karta hai.

### 11.2 Verification Strategies

**Strategy 1: Screenshot Comparison (Visual Verify)**
```
Before: screen_state_before = "Desktop, no Chrome window"
Action: OPEN_APP chrome
After: screenshot lo → screen_state_after
Compare: "Chrome window visible?" → YES → verified
```

**Strategy 2: Window Title Check (Fast)**
```
Action: OPEN_APP chrome
Verify: pygetwindow.getWindowsWithTitle("Chrome") → list empty ya not
Empty → failed → ErrorRecoveryNode
Not empty → verified → next step
```

**Strategy 3: Vision AI Verify (Deep)**
```
For complex actions like SEND_WHATSAPP_FILE:
Take screenshot after action
Ask Groq Llama: "Was a file successfully sent in WhatsApp? Look for checkmarks."
Response: yes/no/uncertain
```

**Strategy 4: Output-Based Verify (No Screenshot)**
```
For system actions like VOLUME_SET:
Just check if function returned without exception
If exception → failed
If success return value → verified
```

### 11.3 Which Strategy When

```python
def decide_verification_strategy(action: str, result: str) -> str:
    """Returns: 'screenshot' | 'window_check' | 'vision_ai' | 'output_based' | 'skip'"""
    
    # System actions — output based kaafi hai
    system_actions = ["VOLUME_SET", "VOLUME_UP", "VOLUME_DOWN", 
                     "BRIGHTNESS_SET", "WIFI_ON", "WIFI_OFF",
                     "MUTE", "UNMUTE", "MEDIA_PLAY", "MEDIA_PAUSE"]
    if action in system_actions:
        return "output_based"
    
    # App opening — window check fast hai
    if action in ["OPEN_APP"]:
        return "window_check"
    
    # URL opening — output based
    if action in ["OPEN_URL"]:
        return "output_based"
    
    # WhatsApp send — deep vision verify
    if action in ["PASTE_AND_SEND", "SEND_MESSAGE", "VERIFY_SENT"]:
        return "vision_ai"
    
    # Screen clicks — screenshot comparison
    if action in ["FIND_AND_CLICK", "CLICK_AT"]:
        return "screenshot"
    
    # Default — screenshot
    return "screenshot"
```

### 11.4 Verify Result → Next Node Decision

```python
def verify_and_route(state: KypzerState) -> str:
    """
    Returns next node name.
    LangGraph conditional edge yeh call karega.
    """
    if state["verification_result"] == "confirmed":
        # Is step ka verification hua — next step pe jao ya respond
        if state["current_step_index"] + 1 < state["total_steps"]:
            state["current_step_index"] += 1
            return "execute"  # next step execute karo
        else:
            return "respond"  # sab steps done, respond karo
    
    elif state["verification_result"] == "skipped":
        # Simple action — no verify needed, just continue
        if state["current_step_index"] + 1 < state["total_steps"]:
            state["current_step_index"] += 1
            return "execute"
        else:
            return "respond"
    
    elif state["verification_result"] == "failed":
        # Verification fail — error recovery pe jao
        if state["retry_count"] < state["max_retries"]:
            return "error_recovery"
        else:
            # Max retries hit — respond with failure
            state["response_text"] = "Kaam nahi hua, please dobara try karo"
            return "respond"
    
    elif state["verification_result"] == "timeout":
        # Screenshot lena fail hua — assume success aur aage badho
        state["verification_result"] = "skipped"
        return "execute" if state["current_step_index"] + 1 < state["total_steps"] else "respond"
```

---

## 12. LANGGRAPH NODE 6 — RESPONDNODE

### 12.1 Purpose

RespondNode ka kaam hai **user ko respond karna** — tts.py use karke.

Yeh node existing `tts.py` ko exactly as-is use karta hai.

### 12.2 Logic

```python
def respond_node(state: KypzerState) -> KypzerState:
    import tts  # existing tts.py
    
    # Response text generate karo agar blank hai
    if not state["response_text"]:
        state["response_text"] = generate_response_text(state)
    
    # Speak karo
    tts.speak_async(state["response_text"])
    
    # Memory mein save karo (existing memory.py)
    import memory
    memory.add_to_memory(
        user_input=state["raw_command"],
        assistant_response=state["response_text"]
    )
    
    # State update
    state["is_complete"] = True
    state["session_commands"].append(state["raw_command"])
    
    return state

def generate_response_text(state: KypzerState) -> str:
    """
    Context se response generate karo.
    Simple cases ke liye rule-based — Gemini call nahi.
    """
    intent = state["intent"]
    params = state["extracted_params"]
    all_success = all(r["result"] == "success" for r in state["all_step_results"])
    
    if all_success:
        # Success responses
        responses = {
            "OPEN_APP": f"{params.get('app_name', 'App')} khol diya!",
            "WHATSAPP_TEXT": f"{params.get('contact', 'Contact')} ko message bhej diya!",
            "WHATSAPP_FILE": f"{params.get('file_keyword', 'File')} bhej diya {params.get('contact', 'unhe')} ko!",
            "OPEN_URL": f"Website khol di!",
            "SCREEN_CLICK": f"Click kar diya!",
        }
        return responses.get(intent, "Kaam ho gaya!")
    else:
        # Partial success
        successful = [r for r in state["all_step_results"] if r["result"] == "success"]
        failed = [r for r in state["all_step_results"] if r["result"] == "failed"]
        
        if len(failed) == 1 and failed[0]["action"].startswith("VERIFY"):
            return "Kaam kar diya, lekin confirm nahi kar paya"
        
        return f"Kuch steps complete hue, lekin {failed[0]['action']} mein dikkat aayi"
```

---

## 13. LANGGRAPH NODE 7 — ERRORRECOVERYNODE

### 13.1 Purpose

ErrorRecoveryNode ka kaam hai **failure ke baad intelligent recovery karna**.

Yeh node tera current system ka sabse bada upgrade hai — abhi koi recovery nahi hai.

### 13.2 Error Types aur Recovery Strategies

**Error Type 1: App Not Found**
```
Error: "Chrome not found"
Recovery: 
  1. Try alternative name: "google-chrome", "Google Chrome"
  2. Try Windows Search
  3. Check if already open (pygetwindow)
  4. Tell user: "Chrome nahi mila, kya manually kholo?"
```

**Error Type 2: Screen Element Not Found**
```
Error: "Play button not found on screen"
Recovery:
  1. Take new screenshot (maybe screen changed)
  2. Try with different description: "play", "triangle button", "media control"
  3. Scroll down to find
  4. Ask user: "Play button visible nahi hua"
```

**Error Type 3: WhatsApp Not Open**
```
Error: "WhatsApp window not found"
Recovery:
  1. Try opening WhatsApp
  2. Wait 3 seconds
  3. Retry find window
  4. If still not found: "WhatsApp nahi khula, please manually kholo"
```

**Error Type 4: API Rate Limit / Timeout**
```
Error: "Gemini API rate limit"
Recovery:
  1. Switch to next API key (existing 4-key rotation)
  2. Retry after 1 second
  3. If all keys exhausted: "Thodi der ke baad try karo"
```

**Error Type 5: Permission Error**
```
Error: "Access denied" / "Permission error"
Recovery:
  1. Log error
  2. Tell user: "Permission chahiye, please admin mode mein chalao"
  3. Abort current task
```

### 13.3 Recovery Logic Implementation

```python
def error_recovery_node(state: KypzerState) -> KypzerState:
    error = state["current_error"]
    intent = state["intent"]
    current_action = state["action_plan"][state["current_step_index"]]["action"]
    
    state["retry_count"] += 1
    
    # Record error
    state["error_history"].append({
        "step": state["current_step_index"],
        "error": error,
        "retry_number": state["retry_count"],
        "timestamp": datetime.now().isoformat()
    })
    
    # Decide recovery strategy
    strategy = decide_recovery_strategy(error, current_action, state["retry_count"])
    state["recovery_strategy"] = strategy
    
    if strategy == "retry_same":
        # Same step dobara try karo
        # Nothing changes except retry_count++
        state["last_action_result"] = ""  # reset
        return state  # go back to execute node
    
    elif strategy == "retry_alternative":
        # Action plan mein current step modify karo
        alternative = get_alternative_action(current_action, error, state["extracted_params"])
        state["action_plan"][state["current_step_index"]] = alternative
        state["last_action_result"] = ""
        return state
    
    elif strategy == "skip_step":
        # Is step ko skip karo
        state["current_step_index"] += 1
        state["last_action_result"] = "skipped"
        return state
    
    elif strategy == "abort":
        state["response_text"] = f"Kaam nahi ho paya: {error}. Please dobara try karo."
        state["is_complete"] = True
        state["next_node"] = "respond"
        return state
    
    elif strategy == "ask_user":
        # Voice se poochho
        import tts
        import stt
        question = generate_user_question(error, current_action)
        tts.speak(question)
        user_response = stt.listen_once()
        # Process user response and modify plan accordingly
        modified_plan = modify_plan_from_user_input(user_response, state)
        state["action_plan"] = modified_plan
        return state

def decide_recovery_strategy(error: str, action: str, retry_count: int) -> str:
    # Max retries hit
    if retry_count >= 3:
        return "abort"
    
    # App not found → try alternative names
    if "not found" in error.lower() and "app" in action.lower():
        return "retry_alternative" if retry_count == 1 else "abort"
    
    # Timeout → retry same
    if "timeout" in error.lower() or "timed out" in error.lower():
        return "retry_same"
    
    # WhatsApp not open → try opening
    if "whatsapp" in error.lower() and "window" in error.lower():
        return "retry_alternative"
    
    # Permission error → abort
    if "permission" in error.lower() or "access denied" in error.lower():
        return "abort"
    
    # Generic → retry same first, then abort
    return "retry_same" if retry_count < 2 else "abort"
```

---

## 14. LANGGRAPH GRAPH ASSEMBLY — FULL FLOW

### 14.1 Complete Graph Code — File: `langgraph_brain.py`

```python
# langgraph_brain.py
# Yeh file brain.py ko REPLACE karta hai main.py mein
# brain.py delete mat karo — fallback ke liye rakhna hai

from langgraph.graph import StateGraph, END
from kypzer_state import KypzerState, create_initial_state
from nodes.understand_node import understand_node
from nodes.see_screen_node import see_screen_node
from nodes.plan_node import plan_node
from nodes.execute_node import execute_node
from nodes.verify_node import verify_node, verify_and_route
from nodes.respond_node import respond_node
from nodes.error_recovery_node import error_recovery_node

def build_kypzer_graph():
    """
    Poora LangGraph banao aur compiled app return karo.
    Ek baar call karo — result cache karo global variable mein.
    """
    
    # Graph initialize karo
    graph = StateGraph(KypzerState)
    
    # Nodes add karo
    graph.add_node("understand", understand_node)
    graph.add_node("see_screen", see_screen_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("verify", verify_node)
    graph.add_node("respond", respond_node)
    graph.add_node("error_recovery", error_recovery_node)
    
    # Entry point
    graph.set_entry_point("understand")
    
    # ─────────────────────────────────────────────
    # EDGES — Node ke baad kahan jaana hai
    # ─────────────────────────────────────────────
    
    # UnderstandNode ke baad:
    # Simple/system commands → direct plan (skip screen)
    # Complex/screen commands → see_screen
    graph.add_conditional_edges(
        "understand",
        lambda state: "plan" if state["should_skip_vision"] else "see_screen",
        {
            "plan": "plan",
            "see_screen": "see_screen"
        }
    )
    
    # SeeScreenNode ke baad → PlanNode (screen context ab available hai)
    graph.add_edge("see_screen", "plan")
    
    # PlanNode ke baad:
    # Multi-agent needed → execute (agent_bridge handle karega internally)
    # Simple → execute
    # Low confidence / need user input → respond directly
    graph.add_conditional_edges(
        "plan",
        lambda state: "respond" if state["intent_confidence"] < 0.4 else "execute",
        {
            "respond": "respond",
            "execute": "execute"
        }
    )
    
    # ExecuteNode ke baad → VerifyNode
    graph.add_edge("execute", "verify")
    
    # VerifyNode ke baad — MAIN ROUTING LOGIC:
    # - Step successful + more steps → execute (next step)
    # - All steps done → respond
    # - Failed → error_recovery
    graph.add_conditional_edges(
        "verify",
        verify_and_route,  # yeh function state mein current_step_index bhi update karta hai
        {
            "execute": "execute",
            "respond": "respond",
            "error_recovery": "error_recovery"
        }
    )
    
    # ErrorRecoveryNode ke baad:
    # Recovery decided → wapas execute pe jao
    # Abort decided → respond pe jao
    graph.add_conditional_edges(
        "error_recovery",
        lambda state: "respond" if state["recovery_strategy"] == "abort" 
                                    or state["is_complete"]
                      else "execute",
        {
            "respond": "respond",
            "execute": "execute"
        }
    )
    
    # RespondNode ke baad → END
    graph.add_edge("respond", END)
    
    return graph.compile()

# Global compiled graph — ek baar banao, baar baar use karo
_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_kypzer_graph()
    return _compiled_graph

def process_command(command: str) -> str:
    """
    Main entry point — main.py yeh function call karega.
    Returns response text (tts.py ke liye).
    
    Yeh brain.py ka process() function replace karta hai.
    """
    try:
        # Initial state banao
        initial_state = create_initial_state(command)
        
        # Graph run karo
        graph = get_graph()
        final_state = graph.invoke(initial_state)
        
        # Response return karo
        return final_state["response_text"]
        
    except Exception as e:
        # Koi bhi error aaye → old brain.py fallback use karo
        print(f"[LangGraph Error] {e} — falling back to brain.py")
        import brain
        return brain.process(command)
```

### 14.2 Graph Visualization (What It Looks Like)

```
[START]
   │
   ▼
[understand_node]
   │
   ├──(should_skip_vision=True)──► [plan_node]
   │                                    │
   └──(should_skip_vision=False)─► [see_screen_node]
                                         │
                                         ▼
                                    [plan_node]
                                         │
                    ┌────────────────────┘
                    │
                    ├──(confidence<0.4)──► [respond_node] ──► [END]
                    │
                    └──(confidence≥0.4)──► [execute_node]
                                                │
                                                ▼
                                          [verify_node]
                                                │
                    ┌───────────────────────────┤
                    │                           │
                    ├── (confirmed+more steps) ─┤
                    │        ▲                  │
                    │        │ (loop)            │
                    │        └──────────────────┘
                    │
                    ├── (confirmed+last step) ──► [respond_node] ──► [END]
                    │
                    └── (failed) ──► [error_recovery_node]
                                              │
                                 ┌────────────┤
                                 │            │
                                 ├──(abort)──►[respond_node] ──► [END]
                                 │
                                 └──(retry)──► [execute_node] (loop back)
```

---

## 15. AUTOGEN AGENT 1 — ORCHESTRATORAGENT

### 15.1 Purpose

OrchestratorAgent = Boss Agent. Yeh decide karta hai kaunsa specialist agent kab kaam kare.

### 15.2 Configuration — File: `agents/orchestrator_agent.py`

```python
# agents/orchestrator_agent.py

import autogen
import os

def create_orchestrator_agent(gemini_api_key: str) -> autogen.AssistantAgent:
    """
    OrchestratorAgent banao.
    Yeh agent purely LLM-based hai — koi tool calls nahi.
    """
    
    config_list = [{
        "model": "gemini-2.0-flash",
        # Tera existing Gemini model use karo
        # AutoGen Gemini support karta hai via litellm
        "api_key": gemini_api_key,
        "api_type": "google"
    }]
    
    orchestrator = autogen.AssistantAgent(
        name="KypzerOrchestrator",
        
        system_message="""
        Tu Kypzer AI ka Chief Orchestrator hai.
        
        Tera kaam:
        1. User ka complex task receive karo
        2. Decide karo kaunse agents ki zaroorat hai
        3. Agents ko ek ek step assign karo
        4. Har step ka result check karo
        5. Agar koi step fail ho, alternative suggest karo
        6. Final result summarize karo
        
        Available Agents:
        - VisionAgent: Screen dekhna, UI elements dhundna, coordinates batana
        - ActionAgent: PC automation — apps kholna, typing, clicking, system control
        - WhatsAppAgent: WhatsApp operations — messages, files, voice notes
        - MemoryAgent: Past conversations dhundna, context retrieve karna
        
        Rules:
        - Ek baar mein ek agent ko kaam do
        - VisionAgent se pehle dekho, phir ActionAgent se karo (jab screen interaction ho)
        - WhatsApp ke liye sirf WhatsAppAgent use karo
        - "TASK_COMPLETE" bol jab sab ho jaye
        - "TASK_FAILED: reason" bol jab impossible ho
        
        Hinglish mein communicate karo agents se.
        JSON format mein instructions do:
        {
          "agent": "VisionAgent",
          "instruction": "Screen pe Gmail ka compose button dhundo",
          "expected_output": "x,y coordinates ya 'not_found'"
        }
        """,
        
        llm_config={
            "config_list": config_list,
            "temperature": 0.1,  # Low temperature — deterministic decisions
            "cache_seed": None   # No caching — fresh decisions
        }
    )
    
    return orchestrator
```

### 15.3 Orchestrator Decision Logic

```
SCENARIO: "Gmail mein compose karo aur papa ko email bhejo"

Orchestrator Turn 1:
  "Task: Gmail mein email compose karo aur papa ko bhejo.
   Step 1: VisionAgent se screen check karo — Gmail open hai?"

VisionAgent response:
  "Chrome open hai, Gmail visible hai, compose button top-left mein hai at (100, 150)"

Orchestrator Turn 2:
  "Step 2: ActionAgent, (100, 150) pe click karo compose button"

ActionAgent response:
  "Clicked at (100, 150), compose window opened"

Orchestrator Turn 3:
  "Step 3: VisionAgent, compose window mein To field dhundo"

VisionAgent response:
  "To field at (400, 200), Subject at (400, 250), Body at (400, 350)"

Orchestrator Turn 4:
  "Step 4: ActionAgent, type karo To field mein papa@gmail.com"

[...continues until task complete...]

Orchestrator Final:
  "TASK_COMPLETE: Email compose window khula, To field ready. User ko papa ka email address batane ke liye TTS se poochho."
```

---

## 16. AUTOGEN AGENT 2 — VISIONAGENT

### 16.1 Purpose

VisionAgent = Specialist screen understanding agent. screen_ai.py ka wrapper.

### 16.2 Configuration — File: `agents/vision_agent.py`

```python
# agents/vision_agent.py

import autogen
import sys
sys.path.append("..")
import screen_ai  # EXISTING — touch nahi kiya

def create_vision_agent(groq_api_key: str, gemini_key: str) -> autogen.AssistantAgent:
    
    config_list = [{
        "model": "gemini-2.0-flash",
        "api_key": gemini_key,
        "api_type": "google"
    }]
    
    vision_agent = autogen.AssistantAgent(
        name="VisionAgent",
        
        system_message="""
        Tu Kypzer AI ka Vision Specialist hai.
        
        Tera kaam:
        - Screen ka screenshot lena
        - UI elements dhundna (buttons, text fields, icons, windows)
        - Element coordinates batana (x, y pixels)
        - Screen ki current state describe karna
        - Wait karna jab tak koi element appear na ho
        
        Jab bhi koi task milega:
        1. Screenshot lo (screen_ai tools use karo)
        2. Task ke relevant elements dhundo
        3. Exact coordinates batao
        4. Agar element nahi mila — clearly batao "NOT_FOUND"
        
        Response format:
        {
          "found": true/false,
          "element": "element name",
          "x": 123,
          "y": 456,
          "confidence": 0.95,
          "screen_description": "brief"
        }
        """,
        
        llm_config={"config_list": config_list}
    )
    
    return vision_agent

# Tool functions jo VisionAgent use karega
def vision_tools():
    """
    Yeh functions UserProxy ke through execute honge.
    screen_ai.py ke existing functions wrap karo.
    """
    
    def take_and_analyze_screenshot(query: str) -> dict:
        """
        Screenshot lo aur analyze karo.
        query: "Find the play button" ya "Is Gmail open?"
        """
        # screen_ai.py ke existing function use karo
        result = screen_ai.find_element(query)
        return result
    
    def check_screen_state(description: str) -> str:
        """
        Screen ka current state check karo.
        description: "Is Chrome open?" ya "What app is in focus?"
        """
        import mss
        import base64
        from groq import Groq
        import io
        from PIL import Image
        
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[0])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            if img.width > 1366:
                ratio = 1366 / img.width
                img = img.resize((1366, int(img.height * ratio)))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
        
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": description}
                ]
            }],
            max_tokens=200
        )
        return response.choices[0].message.content
    
    return [take_and_analyze_screenshot, check_screen_state]
```

---

## 17. AUTOGEN AGENT 3 — ACTIONAGENT

### 17.1 Purpose

ActionAgent = Specialist automation agent. actions.py ka wrapper.

### 17.2 Configuration — File: `agents/action_agent.py`

```python
# agents/action_agent.py

import autogen
import sys
sys.path.append("..")
import actions  # EXISTING — touch nahi kiya
import pyautogui

def create_action_agent(gemini_key: str) -> autogen.AssistantAgent:
    
    config_list = [{"model": "gemini-2.0-flash", "api_key": gemini_key, "api_type": "google"}]
    
    action_agent = autogen.AssistantAgent(
        name="ActionAgent",
        
        system_message="""
        Tu Kypzer AI ka Action Specialist hai.
        
        Tera kaam:
        - Mouse click karna given coordinates pe
        - Text type karna
        - Keyboard shortcuts press karna
        - Apps kholna/bandh karna
        - System controls (volume, brightness, wifi)
        - Screenshots lena
        
        Jab coordinates mile (from VisionAgent), directly click karo.
        Jab app name mile, actions.py functions use karo.
        
        Har action ke baad batao:
        {
          "action_performed": "clicked at (100, 150)",
          "result": "success/failed",
          "output": "what happened"
        }
        
        Safety rules:
        - Kabhi bhi system32 ya critical folders delete mat karo
        - Confirm karo agar destructive action ho (delete, format, etc.)
        - Double-check coordinates before clicking
        """,
        
        llm_config={"config_list": config_list}
    )
    
    return action_agent

def action_tools():
    """
    ActionAgent ke tools — actions.py functions wrap karo.
    """
    
    def click_at_coordinates(x: int, y: int) -> str:
        """Click at given screen coordinates"""
        try:
            pyautogui.click(x, y)
            return f"Clicked at ({x}, {y})"
        except Exception as e:
            return f"Click failed: {e}"
    
    def type_text_clipboard(text: str) -> str:
        """Type text using clipboard (Unicode support)"""
        try:
            actions.type_text(text)  # existing function
            return f"Typed: {text[:50]}..."
        except Exception as e:
            return f"Type failed: {e}"
    
    def open_application(app_name: str) -> str:
        """Open an application by name"""
        try:
            actions.open_app(app_name)  # existing function
            return f"Opened {app_name}"
        except Exception as e:
            return f"Open failed: {e}"
    
    def press_keyboard_shortcut(shortcut: str) -> str:
        """
        Press keyboard shortcut.
        shortcut: "ctrl+c" / "alt+tab" / "win+d" etc.
        """
        try:
            import keyboard
            keyboard.press_and_release(shortcut)
            return f"Pressed: {shortcut}"
        except Exception as e:
            return f"Shortcut failed: {e}"
    
    def execute_system_action(action_name: str, value=None) -> str:
        """
        Execute system actions from actions.py.
        action_name: same as action names in actions.py
        """
        try:
            action_map = {
                "VOLUME_UP": lambda: actions.change_volume(+10),
                "VOLUME_DOWN": lambda: actions.change_volume(-10),
                "MUTE": lambda: actions.mute_volume(),
                # ... add more from actions.py
            }
            if action_name in action_map:
                action_map[action_name]()
                return f"Executed: {action_name}"
            else:
                return f"Unknown action: {action_name}"
        except Exception as e:
            return f"Action failed: {e}"
    
    return [click_at_coordinates, type_text_clipboard, open_application, 
            press_keyboard_shortcut, execute_system_action]
```

---

## 18. AUTOGEN AGENT 4 — WHATSAPPAGENT

### 18.1 Purpose

WhatsAppAgent = Specialist WhatsApp automation agent. whatsapp_module ka wrapper.

### 18.2 Configuration — File: `agents/whatsapp_agent.py`

```python
# agents/whatsapp_agent.py

import autogen
import sys
sys.path.append("..")
from whatsapp_module import handler, wa_controller, file_search

def create_whatsapp_agent(gemini_key: str) -> autogen.AssistantAgent:
    
    config_list = [{"model": "gemini-2.0-flash", "api_key": gemini_key, "api_type": "google"}]
    
    whatsapp_agent = autogen.AssistantAgent(
        name="WhatsAppAgent",
        
        system_message="""
        Tu Kypzer AI ka WhatsApp Specialist hai.
        
        Tera kaam:
        - WhatsApp Desktop kholo aur contacts dhundo
        - Text messages bhejo
        - Voice notes bhejo (text-to-voice conversion ke baad)
        - Files dhundo (PC-wide search) aur bhejo
        - Confirmation lo user se agar multiple files milein
        
        Available operations:
        1. send_text(contact, message) — text message
        2. send_voice_note(contact, text) — convert to voice and send
        3. search_and_send_file(contact, keyword) — find file and send
        4. open_whatsapp_chat(contact) — just open chat
        
        Har operation ke baad status batao:
        {
          "operation": "send_text",
          "contact": "papa",
          "status": "success/failed",
          "details": "Message sent successfully"
        }
        
        Agar multiple files milein:
        - User ko TTS se options bolo
        - Voice input se selection lo
        - Fir selected file bhejo
        """,
        
        llm_config={"config_list": config_list}
    )
    
    return whatsapp_agent

def whatsapp_tools():
    """
    WhatsApp tools — whatsapp_module ke existing functions wrap karo.
    """
    
    def send_whatsapp_text(contact: str, message: str) -> str:
        """Send a text message on WhatsApp"""
        try:
            # whatsapp_module/handler.py ka existing logic use karo
            result = handler.handle_send_command(
                f"{contact} ko message bhejo ki {message}"
            )
            return f"Message sent to {contact}"
        except Exception as e:
            return f"Send failed: {e}"
    
    def search_and_send_file(contact: str, file_keyword: str) -> str:
        """Search for a file on PC and send via WhatsApp"""
        try:
            # file_search.py ka existing logic use karo
            files = file_search.search_files(file_keyword)
            if not files:
                return f"No files found matching '{file_keyword}'"
            
            if len(files) == 1:
                # Single file — directly send
                result = handler.handle_send_command(
                    f"{contact} ko {file_keyword} bhejo"
                )
                return f"File sent: {files[0]}"
            else:
                # Multiple files — yeh already handler.py handle karta hai with voice
                result = handler.handle_send_command(
                    f"{contact} ko {file_keyword} bhejo"
                )
                return f"File sent to {contact}"
        except Exception as e:
            return f"File send failed: {e}"
    
    def open_whatsapp_contact(contact: str) -> str:
        """Open WhatsApp and navigate to contact"""
        try:
            wa_controller.open_whatsapp_chat(contact)  # existing function
            return f"Opened WhatsApp chat with {contact}"
        except Exception as e:
            return f"WhatsApp open failed: {e}"
    
    return [send_whatsapp_text, search_and_send_file, open_whatsapp_contact]
```

---

## 19. AUTOGEN AGENT 5 — MEMORYAGENT

### 19.1 Purpose

MemoryAgent = Specialist memory retrieval agent. memory.py ka wrapper.

### 19.2 Configuration — File: `agents/memory_agent.py`

```python
# agents/memory_agent.py

import autogen
import sys
sys.path.append("..")
import memory  # existing memory.py

def create_memory_agent(gemini_key: str) -> autogen.AssistantAgent:
    
    config_list = [{"model": "gemini-2.0-flash", "api_key": gemini_key, "api_type": "google"}]
    
    memory_agent = autogen.AssistantAgent(
        name="MemoryAgent",
        
        system_message="""
        Tu Kypzer AI ka Memory Specialist hai.
        
        Tera kaam:
        - Past conversations retrieve karna (ChromaDB se)
        - Context provide karna current command ke liye
        - User preferences yaad rakhna
        - Conversation history store karna
        
        Operations:
        1. retrieve_context(query) — relevant past conversations
        2. store_conversation(user_input, assistant_response)
        3. get_user_preference(topic) — past preferences
        4. get_recent_commands(n) — last n commands
        
        Context format:
        {
          "relevant_history": ["command1", "command2"],
          "user_preferences": {"language": "hinglish", "frequent_apps": ["chrome", "whatsapp"]},
          "last_action": "what was done last"
        }
        """,
        
        llm_config={"config_list": config_list}
    )
    
    return memory_agent

def memory_tools():
    
    def retrieve_relevant_context(query: str, n_results: int = 3) -> dict:
        """Retrieve relevant past conversations from ChromaDB"""
        try:
            # memory.py ka existing retrieve function use karo
            results = memory.retrieve_relevant_history(query, n_results)
            return {"context": results, "found": len(results) > 0}
        except Exception as e:
            return {"context": [], "found": False, "error": str(e)}
    
    def store_conversation(user_input: str, response: str) -> str:
        """Store conversation in ChromaDB"""
        try:
            memory.add_to_memory(user_input, response)  # existing function
            return "Stored successfully"
        except Exception as e:
            return f"Store failed: {e}"
    
    def get_session_context(session_commands: list) -> str:
        """Generate context string from session commands"""
        if not session_commands:
            return "No previous commands in this session"
        last_3 = session_commands[-3:]
        return f"Recent commands: {', '.join(last_3)}"
    
    return [retrieve_relevant_context, store_conversation, get_session_context]
```

---

## 20. AUTOGEN GROUPCHAT — MULTI-AGENT COORDINATION

### 20.1 When GroupChat Activate Hota Hai

```
state.needs_multi_agent = True hone par:
  - FLOW_ASMR (15-step complex automation)
  - Complex SCREEN_* interactions (multiple screen states)
  - MULTI_STEP commands (multiple apps involved)
  - Error recovery mein complex alternatives
```

### 20.2 GroupChat Configuration — File: `agents/group_chat.py`

```python
# agents/group_chat.py

import autogen
from agents.orchestrator_agent import create_orchestrator_agent
from agents.vision_agent import create_vision_agent, vision_tools
from agents.action_agent import create_action_agent, action_tools
from agents.whatsapp_agent import create_whatsapp_agent, whatsapp_tools
from agents.memory_agent import create_memory_agent, memory_tools

def create_kypzer_groupchat(gemini_key: str, groq_key: str) -> tuple:
    """
    Poora GroupChat setup karo.
    Returns: (groupchat, manager)
    """
    
    # Create all agents
    orchestrator = create_orchestrator_agent(gemini_key)
    vision_agent = create_vision_agent(groq_key, gemini_key)
    action_agent = create_action_agent(gemini_key)
    whatsapp_agent = create_whatsapp_agent(gemini_key)
    memory_agent = create_memory_agent(gemini_key)
    
    # UserProxy — actual tools execute karta hai
    user_proxy = autogen.UserProxyAgent(
        name="KypzerProxy",
        human_input_mode="NEVER",  # automatic — koi human input nahi
        max_consecutive_auto_reply=15,  # max 15 agent turns
        
        # Tool functions register karo
        function_map={
            # Vision tools
            **{f.__name__: f for f in vision_tools()},
            # Action tools
            **{f.__name__: f for f in action_tools()},
            # WhatsApp tools
            **{f.__name__: f for f in whatsapp_tools()},
            # Memory tools
            **{f.__name__: f for f in memory_tools()},
        },
        
        # Termination condition
        is_termination_msg=lambda msg: (
            "TASK_COMPLETE" in msg.get("content", "") or
            "TASK_FAILED" in msg.get("content", "")
        ),
        
        code_execution_config=False  # No code execution — sirf function calls
    )
    
    # GroupChat — agents ki list
    groupchat = autogen.GroupChat(
        agents=[user_proxy, orchestrator, vision_agent, action_agent, 
                whatsapp_agent, memory_agent],
        messages=[],
        max_round=20,  # max 20 conversation rounds
        
        # Speaker selection — Orchestrator decide karta hai kaun bolega
        speaker_selection_method="auto",
        
        # Allow repeated speakers — same agent dobara bol sakta hai
        allow_repeat_speaker=True,
    )
    
    # GroupChatManager — orchestrates the chat
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={
            "config_list": [{"model": "gemini-2.0-flash", "api_key": gemini_key, "api_type": "google"}],
            "temperature": 0.1
        }
    )
    
    return user_proxy, groupchat, manager

def run_multi_agent_task(task: str, context: dict, gemini_key: str, groq_key: str) -> dict:
    """
    Multi-agent task run karo.
    Returns: {result, conversation_history, success}
    """
    user_proxy, groupchat, manager = create_kypzer_groupchat(gemini_key, groq_key)
    
    # Task message prepare karo
    task_message = f"""
    Task: {task}
    
    Context:
    - Intent: {context.get('intent')}
    - Parameters: {context.get('extracted_params')}
    - Screen State: {context.get('screen_context', 'Unknown')}
    - Past Context: {context.get('memory_context', 'None')}
    
    Execute this task step by step. 
    Use VisionAgent to see screen, ActionAgent to perform actions.
    End with TASK_COMPLETE or TASK_FAILED.
    """
    
    # Chat start karo
    user_proxy.initiate_chat(
        manager,
        message=task_message
    )
    
    # Results extract karo
    conversation = [
        {"agent": msg["name"], "content": msg["content"]}
        for msg in groupchat.messages
    ]
    
    # Success check
    last_messages = groupchat.messages[-3:]
    success = any("TASK_COMPLETE" in m.get("content", "") for m in last_messages)
    
    return {
        "success": success,
        "conversation": conversation,
        "result": groupchat.messages[-1]["content"] if groupchat.messages else ""
    }
```

---

## 21. LANGGRAPH + AUTOGEN BRIDGE

### 21.1 Purpose

Agent Bridge = LangGraph nodes aur AutoGen agents ke beech connection.

Jab LangGraph ka PlanNode decide karta hai ki `needs_multi_agent = True`, toh ExecuteNode agent_bridge.py ko call karta hai.

### 21.2 File: `agent_bridge.py`

```python
# agent_bridge.py
# LangGraph ka ExecuteNode yeh file call karta hai complex tasks ke liye

import os
from dotenv import load_dotenv
from agents.group_chat import run_multi_agent_task
from kypzer_state import KypzerState

load_dotenv("env.env")

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

def execute_with_multi_agent(state: KypzerState) -> KypzerState:
    """
    Complex tasks ke liye AutoGen GroupChat use karo.
    State update karke return karo.
    """
    
    # Task description banao
    current_step = state["action_plan"][state["current_step_index"]]
    task = f"""
    Execute this task for Kypzer AI:
    Action: {current_step['action']}
    Value: {current_step.get('value')}
    User Command: {state['raw_command']}
    Contact (if applicable): {state['extracted_params'].get('contact')}
    File Keyword (if applicable): {state['extracted_params'].get('file_keyword')}
    """
    
    context = {
        "intent": state["intent"],
        "extracted_params": state["extracted_params"],
        "screen_context": state["screen_context"],
        "memory_context": state["memory_context"]
    }
    
    # Multi-agent task run karo
    result = run_multi_agent_task(task, context, GEMINI_KEY, GROQ_KEY)
    
    # State update karo
    state["agent_conversation"] = result["conversation"]
    
    if result["success"]:
        state["last_action_result"] = "success"
        state["last_action_output"] = result["result"]
    else:
        state["last_action_result"] = "failed"
        state["last_action_output"] = result["result"]
        state["current_error"] = f"Multi-agent task failed: {result['result']}"
    
    # Step results record karo
    state["all_step_results"].append({
        "step": current_step["step"],
        "action": current_step["action"],
        "result": state["last_action_result"],
        "output": state["last_action_output"],
        "used_multi_agent": True
    })
    
    return state

def execute_with_single_agent(state: KypzerState, agent_name: str) -> KypzerState:
    """
    Single agent use karo agar full GroupChat overkill hai.
    agent_name: "VisionAgent" / "ActionAgent" / "WhatsAppAgent"
    """
    # Simplified single-agent execution
    current_step = state["action_plan"][state["current_step_index"]]
    
    if agent_name == "WhatsAppAgent":
        from agents.whatsapp_agent import whatsapp_tools
        tools = {f.__name__: f for f in whatsapp_tools()}
        
        # Route based on action
        action = current_step["action"]
        params = state["extracted_params"]
        
        if action == "SEND_WHATSAPP_TEXT":
            result = tools["send_whatsapp_text"](params["contact"], params["message"])
        elif action in ["WHATSAPP_FILE", "SEND_WHATSAPP_FILE_SMART"]:
            result = tools["search_and_send_file"](params["contact"], params["file_keyword"])
        else:
            result = f"Unknown WhatsApp action: {action}"
        
        state["last_action_result"] = "success" if "failed" not in result.lower() else "failed"
        state["last_action_output"] = result
    
    return state
```

---

## 22. NEW BRAIN.PY — REPLACING OLD GEMINI BRAIN

### 22.1 Strategy

Old `brain.py` ko DELETE NAHI KARNA — fallback ke liye rakhna hai.

New approach:
- `langgraph_brain.py` main entry point banega
- `brain.py` fallback ke liye intact rahega
- Wrapper function likhna hai jo:
  - Pehle LangGraph try kare
  - Agar fail → old brain.py

### 22.2 brain_wrapper.py — File

```python
# brain_wrapper.py
# main.py mein brain.process() ko brain_wrapper.smart_process() se replace karo

import logging

# LangGraph import try karo — agar installed nahi toh fallback
try:
    from langgraph_brain import process_command as langgraph_process
    LANGGRAPH_AVAILABLE = True
    print("[Brain] LangGraph available — using intelligent routing")
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("[Brain] LangGraph not available — using classic brain.py")

# Old brain.py always available rakho
import brain as classic_brain

def smart_process(command: str) -> str:
    """
    Main function — main.py yeh call karega.
    
    Routing logic:
    1. Simple/system commands → classic brain.py (fast, no LangGraph overhead)
    2. Complex commands → LangGraph pipeline
    3. LangGraph fail → classic brain.py fallback
    """
    
    # Simple commands jo LangGraph ki zaroorat nahi
    # (yeh already intent.py handle karta hai, but double safety)
    simple_intents = ["volume", "brightness", "wifi", "bluetooth", "mute", 
                     "shutdown", "restart", "sleep", "lock", "screenshot",
                     "play", "pause", "next", "previous", "stop"]
    
    command_lower = command.lower()
    is_simple = any(word in command_lower for word in simple_intents)
    
    if is_simple or not LANGGRAPH_AVAILABLE:
        # Classic brain se process karo
        return classic_brain.process(command)
    
    # Complex command — LangGraph use karo
    try:
        result = langgraph_process(command)
        return result
    
    except Exception as e:
        logging.error(f"LangGraph failed: {e}")
        # Fallback to classic
        return classic_brain.process(command)

# Direct export — main.py mein drop-in replacement
def process(command: str) -> str:
    """Legacy interface — existing brain.process() calls work without change"""
    return smart_process(command)
```

---

## 23. NEW SCREEN_AI.PY — VISION NODE WRAPPER

### 23.1 Strategy

`screen_ai.py` bilkul TOUCH NAHI KARNA.

`see_screen_node.py` aur `vision_agent.py` screen_ai.py ko import karke use karenge.

### 23.2 Additional Helper — `vision_helpers.py`

Yeh file screen_ai.py ke existing functions ke upar wrapper provide karta hai:

```python
# vision_helpers.py
# screen_ai.py ko wrap karta hai LangGraph nodes ke liye

import sys
sys.path.append("..")
import screen_ai  # EXISTING — untouched

def get_current_screen_state(intent: str = "", params: dict = None) -> dict:
    """
    Returns structured screen state for LangGraph nodes.
    """
    params = params or {}
    
    # screen_ai.py ke existing analyze function use karo
    # (Adjust based on actual screen_ai.py API)
    
    try:
        # Option 1: Agar screen_ai.py mein analyze_screen function hai
        if hasattr(screen_ai, 'analyze_screen'):
            description = screen_ai.analyze_screen(
                f"Describe screen for: {intent} {params}"
            )
            return {
                "description": description,
                "elements": [],
                "success": True
            }
        
        # Option 2: Agar screen_ai.py mein find_element hai
        elif hasattr(screen_ai, 'find_element'):
            # Generic screen analysis
            result = screen_ai.find_element("current screen state")
            return {
                "description": str(result),
                "elements": [result] if result else [],
                "success": True
            }
        
        # Option 3: Direct Groq call (screen_ai.py ki tarah)
        else:
            return _direct_groq_screen_analysis(intent, params)
    
    except Exception as e:
        return {
            "description": f"Screen analysis failed: {e}",
            "elements": [],
            "success": False
        }

def find_ui_element(description: str) -> dict:
    """
    Find a UI element on screen and return coordinates.
    Returns: {"found": bool, "x": int, "y": int, "confidence": float}
    """
    try:
        result = screen_ai.find_element(description)  # existing function
        if result and isinstance(result, dict):
            return {
                "found": result.get("found", False),
                "x": result.get("x", 0),
                "y": result.get("y", 0),
                "confidence": result.get("confidence", 0.0)
            }
        return {"found": False, "x": 0, "y": 0, "confidence": 0.0}
    except Exception as e:
        return {"found": False, "x": 0, "y": 0, "confidence": 0.0, "error": str(e)}

def verify_screen_change(before_description: str, expected_change: str) -> dict:
    """
    Verify karo ki screen pe expected change aaya kya.
    Returns: {"verified": bool, "current_state": str, "details": str}
    """
    # Fresh screenshot lo aur compare karo
    current_state = get_current_screen_state()
    current_desc = current_state["description"]
    
    # Simple keyword check
    expected_keywords = expected_change.lower().split()
    matches = sum(1 for kw in expected_keywords if kw in current_desc.lower())
    match_ratio = matches / len(expected_keywords) if expected_keywords else 0
    
    return {
        "verified": match_ratio > 0.5,
        "current_state": current_desc,
        "match_ratio": match_ratio,
        "details": f"Expected: {expected_change}, Found match ratio: {match_ratio:.2f}"
    }

def _direct_groq_screen_analysis(intent: str, params: dict) -> dict:
    """
    Direct Groq call — screen_ai.py ka koi function nahi toh yeh use karo.
    screen_ai.py ka implementation dekh ke copy karo GROQ key aur model.
    """
    import mss, base64, json, io, os
    from PIL import Image
    from groq import Groq
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        if img.width > 1366:
            ratio = 1366 / img.width
            img = img.resize((1366, int(img.height * ratio)))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode()
    
    client = Groq(api_key=groq_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": f"""
                    Describe this screen for a PC automation system.
                    User intent: {intent}
                    Parameters: {params}
                    
                    Return JSON:
                    {{
                        "description": "screen description",
                        "visible_windows": [],
                        "key_elements": []
                    }}
                """}
            ]
        }],
        max_tokens=400
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
        return {"description": result.get("description", ""), "elements": result.get("key_elements", []), "success": True}
    except:
        return {"description": response.choices[0].message.content, "elements": [], "success": True}
```

---

## 24. NEW MEMORY.PY — STATE-AWARE MEMORY

### 24.1 Strategy

`memory.py` ko enhance karo — nayi methods add karo, existing code touch mat karo.

### 24.2 Additions to memory.py

```python
# memory.py ke BOTTOM mein yeh functions ADD karo
# Existing code TOUCH NAHI KARNA

# ─────────────────────────────────────────────────────────────────
# NEW ADDITIONS FOR LANGGRAPH INTEGRATION
# (Yeh add karo existing functions ke baad)
# ─────────────────────────────────────────────────────────────────

def get_relevant_context(query: str, max_results: int = 3) -> str:
    """
    LangGraph ke UnderstandNode ke liye — relevant past context return karo.
    Returns formatted string for state.memory_context field.
    """
    try:
        # Existing retrieve function use karo
        # (Actual function name teri memory.py se match karo)
        results = retrieve_relevant_history(query, max_results)
        
        if not results:
            return "No relevant past context found"
        
        context_parts = []
        for i, result in enumerate(results[:3]):
            if isinstance(result, dict):
                user_msg = result.get("user", result.get("input", ""))
                asst_msg = result.get("assistant", result.get("response", ""))
                context_parts.append(f"Past {i+1}: User: {user_msg[:50]} → {asst_msg[:50]}")
            else:
                context_parts.append(f"Past {i+1}: {str(result)[:100]}")
        
        return " | ".join(context_parts)
    
    except Exception as e:
        return f"Memory retrieval error: {e}"

def save_command_session(session_id: str, commands: list, final_result: str):
    """
    Ek poore session ka summary save karo.
    LangGraph ke RespondNode se call hoga.
    """
    try:
        session_summary = {
            "session_id": session_id,
            "commands": commands,
            "result": final_result,
            "timestamp": datetime.now().isoformat()
        }
        # Existing add_to_memory function use karo
        combined_input = " → ".join(commands)
        add_to_memory(combined_input, final_result)
    except Exception as e:
        print(f"[Memory] Session save failed: {e}")

def get_user_preferences() -> dict:
    """
    User ke preferences retrieve karo past conversations se.
    Returns common patterns.
    """
    # Simple heuristic — frequently used commands
    return {
        "language": "hinglish",  # Default
        "frequent_contacts": [],
        "frequent_apps": []
    }
```

---

## 25. MAIN.PY CHANGES — MINIMAL TOUCH

### 25.1 What to Change

Sirf **ek line** change karni hai main.py mein:

```python
# PURANI LINE (teri main.py mein dhundo):
result = brain.process(command)

# NAYI LINE (replace karo):
result = brain_wrapper.smart_process(command)
```

### 25.2 Import Change

```python
# main.py ke top pe — existing import ke saath:

# PURANA:
import brain

# NAYA (purana mat hatao — wrapper handle karega):
import brain_wrapper
```

### 25.3 Complete main.py Modified Section

```python
# main.py mein yeh section dhundo (jahan brain.process call hota hai)
# Exactly yahan pe change karo — baaki kuch nahi

# Purana code:
# ---
# if intent_result:
#     response = intent_result
# else:
#     response = brain.process(command)
# ---

# Naya code:
# ---
if intent_result:
    response = intent_result
else:
    # Smart process — tries LangGraph first, falls back to classic brain
    response = brain_wrapper.smart_process(command)  
# ---
```

### 25.4 Fast Routes — BILKUL TOUCH NAHI

```
main.py ke yeh functions mat chhuo:
  ✓ _fast_browser_route() — UNCHANGED
  ✓ _fast_whatsapp_route() — UNCHANGED
  ✓ main loop — UNCHANGED
  ✓ tts.speak() calls — UNCHANGED
  ✓ mic.record() calls — UNCHANGED
  ✓ stt.transcribe() calls — UNCHANGED
```

---

## 26. WHATSAPP MODULE — AGENT WRAPPER

### 26.1 Strategy

`whatsapp_module/` ke koi bhi file touch nahi karne.

`agents/whatsapp_agent.py` already pure wrapper hai — woh existing functions import karke use karta hai.

### 26.2 Only Addition — `whatsapp_module/__init__.py` Update

```python
# whatsapp_module/__init__.py mein add karo (agar exist karta hai)
# Nahin toh create karo

# Existing imports preserve karo, bas yeh add karo:

def send_file_to_contact(contact: str, file_keyword: str) -> bool:
    """
    Convenience function for AutoGen WhatsAppAgent.
    Existing handler.py ko call karta hai.
    """
    try:
        from whatsapp_module import handler
        full_command = f"{contact} ko {file_keyword} bhejo"
        handler.handle_send_command(full_command)
        return True
    except Exception:
        return False

def send_message_to_contact(contact: str, message: str) -> bool:
    """
    Convenience function for AutoGen WhatsAppAgent.
    """
    try:
        from whatsapp_module import handler
        full_command = f"{contact} ko message bhejo ki {message}"
        handler.handle_send_command(full_command)
        return True
    except Exception:
        return False
```

---

## 27. RETRY & ERROR RECOVERY LOGIC — FULL DETAIL

### 27.1 Retry Flow — Complete Decision Tree

```
ACTION EXECUTE KIYA
      │
      ▼
VERIFICATION ATTEMPT
      │
   ┌──┴──┐
   │     │
SUCCESS FAILED
   │     │
   ▼     ▼
CONTINUE  retry_count < max_retries?
          │
       ┌──┴──┐
      YES    NO
       │      │
       ▼      ▼
  ERROR_     RESPOND
  RECOVERY   "Fail hua"
  NODE
       │
       ▼
  Analyze Error Type:
  ┌─────────────────────────────────────┐
  │ "app not found" → try alternatives  │
  │ "timeout" → retry same             │
  │ "window not found" → reopen app    │
  │ "element not found" → re-screenshot│
  │ "permission" → abort               │
  │ "api error" → switch key + retry   │
  └─────────────────────────────────────┘
       │
       ▼
  Apply Strategy
       │
  ┌────┤
  │    │
  │  retry_alternative:
  │    Modify action_plan[current_step]
  │    Alternative action define karo
  │    Go back to ExecuteNode
  │
  │  retry_same:
  │    Same action dobara try karo
  │    last_action_result reset karo
  │    Go back to ExecuteNode
  │
  │  skip_step:
  │    current_step_index++
  │    Verification skip
  │    Go to next step
  │
  │  ask_user:
  │    TTS se question poocho
  │    STT se answer lo
  │    Plan modify karo
  │    Go back to PlanNode
  │
  └  abort:
       response_text = failure message
       Go to RespondNode
```

### 27.2 Alternative Actions Library

```python
# error_recovery_node.py mein yeh alternatives dictionary rakho

ALTERNATIVE_ACTIONS = {
    "OPEN_APP": {
        "app_not_found": [
            # Try different names
            lambda params: {"action": "OPEN_APP", "value": params["app_name"] + ".exe"},
            # Try Windows search
            lambda params: {"action": "PRESS_KEY", "value": f"win", "then_type": params["app_name"]},
            # Check if already open
            lambda params: {"action": "FIND_AND_CLICK", "value": f"{params['app_name']} in taskbar"}
        ]
    },
    
    "FIND_AND_CLICK": {
        "element_not_found": [
            # Scroll down and try again
            lambda params: {"action": "SCROLL_DOWN", "value": 3, "then_retry": True},
            # Try alternate description
            lambda params: {"action": "FIND_AND_CLICK", "value": f"any {params['click_target']} button"},
            # Use keyboard shortcut instead
            lambda params: {"action": "PRESS_KEY", "value": params.get("keyboard_alt", "tab")}
        ]
    },
    
    "OPEN_WHATSAPP_CHAT": {
        "whatsapp_window_not_found": [
            # Try opening WhatsApp first
            lambda params: {"action": "OPEN_APP", "value": "WhatsApp", "then_retry_original": True}
        ]
    },
    
    "PASTE_AND_SEND": {
        "paste_failed": [
            # Try Ctrl+V manually
            lambda params: {"action": "PRESS_KEY", "value": "ctrl+v"},
            # Then Enter
            {"action": "PRESS_KEY", "value": "enter"}
        ]
    }
}

def get_alternative_action(failed_action: str, error: str, params: dict) -> dict:
    """
    Failed action aur error ke basis pe alternative action return karo.
    """
    if failed_action not in ALTERNATIVE_ACTIONS:
        return {"action": failed_action, **params}  # Same action — no alternative
    
    alternatives = ALTERNATIVE_ACTIONS[failed_action]
    
    # Error type match karo
    for error_pattern, alt_actions in alternatives.items():
        if error_pattern.replace("_", " ") in error.lower():
            # First alternative try karo
            alt = alt_actions[0] if isinstance(alt_actions, list) else alt_actions
            if callable(alt):
                return alt(params)
            return alt
    
    return {"action": failed_action, **params}  # Default — same action
```

---

## 28. STATE PERSISTENCE — CONVERSATION CONTEXT

### 28.1 Cross-Command Context

LangGraph khud ek command ke andar state maintain karta hai. Cross-command context ke liye ChromaDB use karo.

```python
# kypzer_state.py mein add karo:

SESSION_STORE = {}  # In-memory session store

def save_session_state(session_id: str, final_state: KypzerState):
    """
    Command complete hone ke baad important parts save karo.
    Next command mein context ke liye.
    """
    SESSION_STORE[session_id] = {
        "intent": final_state["intent"],
        "result": final_state["last_action_output"],
        "command": final_state["raw_command"],
        "timestamp": final_state["command_timestamp"],
        "screen_state": final_state["screen_state_after"],
        "params": final_state["extracted_params"]
    }
    
    # Last 5 sessions rakhna — purane delete karo
    if len(SESSION_STORE) > 5:
        oldest_key = list(SESSION_STORE.keys())[0]
        del SESSION_STORE[oldest_key]

def get_session_context_for_next_command() -> str:
    """
    Next command ke liye context string generate karo.
    UnderstandNode se call hoga.
    """
    if not SESSION_STORE:
        return "No previous commands"
    
    recent = list(SESSION_STORE.values())[-3:]  # last 3
    parts = []
    for s in recent:
        parts.append(f"{s['command']} → {s['result'][:30]}")
    
    return "; ".join(parts)
```

### 28.2 Screen State Tracking

```python
# actions.py TOUCH NAHI KARNA
# Yeh tracking langgraph_brain.py mein karo

class ScreenStateTracker:
    """
    Screen changes track karo across commands.
    Main.py instance banaye — ek command se doosre command mein state carry ho.
    """
    
    def __init__(self):
        self.current_focused_app = "desktop"
        self.open_windows = []
        self.last_url = ""
        self.last_whatsapp_contact = ""
    
    def update_from_state(self, final_state: KypzerState):
        intent = final_state["intent"]
        params = final_state["extracted_params"]
        
        if intent == "OPEN_APP" and final_state["last_action_result"] == "success":
            self.current_focused_app = params.get("app_name", self.current_focused_app)
        
        if intent == "OPEN_URL" and final_state["last_action_result"] == "success":
            self.last_url = params.get("url", "")
        
        if intent in ["WHATSAPP_TEXT", "WHATSAPP_FILE"]:
            self.last_whatsapp_contact = params.get("contact", "")
    
    def get_context_string(self) -> str:
        return (f"Focused app: {self.current_focused_app}, "
                f"Last URL: {self.last_url or 'none'}, "
                f"Last WhatsApp: {self.last_whatsapp_contact or 'none'}")
```

---

## 29. PERFORMANCE OPTIMIZATION PLAN

### 29.1 LangGraph Overhead Analysis

```
Abhi:
  Simple command (volume) → intent.py → 0.5s ✅
  Complex command → brain.py → 2-3s ✅

LangGraph ke saath:
  Simple command → SAME (fast path unchanged) → 0.5s ✅
  Complex command → LangGraph → 3-5s ⚠️ (kuch zyada)

Why more? 
  - State object creation: ~10ms
  - Node execution overhead: ~50ms per node
  - Verification (screenshot): +1-2s
  
Acceptable? YES — kyunki:
  - Complex commands abhi bhi 2-3s + no verification
  - LangGraph: 3-5s + full verification + retry
  - Net result: more reliable, slightly slower
```

### 29.2 Optimization Strategies

**Optimization 1: Skip Vision for Known Simple Actions**
```python
# plan_node.py mein — agar intent clearly simple hai, skip verify
SKIP_VERIFY_INTENTS = ["VOLUME_SET", "BRIGHTNESS_SET", "WIFI_TOGGLE", 
                       "MEDIA_CONTROL", "OPEN_URL"]  # URL bas khulta hai, verify nahi

if intent in SKIP_VERIFY_INTENTS:
    state["verification_result"] = "skipped"  # Pre-set
```

**Optimization 2: Parallel Processing Where Possible**
```python
# see_screen_node.py mein — memory retrieval aur screenshot parallel lo
import asyncio
import concurrent.futures

def see_screen_and_get_memory(state):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        screenshot_future = executor.submit(take_screenshot)
        memory_future = executor.submit(memory.get_relevant_context, state["raw_command"])
        
        screenshot = screenshot_future.result()
        memory_ctx = memory_future.result()
    
    # Dono parallel complete ho gayi
    state["screen_screenshot_path"] = screenshot
    state["memory_context"] = memory_ctx
```

**Optimization 3: Plan Caching**
```python
# plan_node.py mein — same intent + params → same plan use karo
import hashlib

PLAN_CACHE = {}

def get_cached_plan(intent: str, params: dict) -> list:
    cache_key = hashlib.md5(f"{intent}{str(sorted(params.items()))}".encode()).hexdigest()
    return PLAN_CACHE.get(cache_key)

def cache_plan(intent: str, params: dict, plan: list):
    cache_key = hashlib.md5(f"{intent}{str(sorted(params.items()))}".encode()).hexdigest()
    PLAN_CACHE[cache_key] = plan
    # Max 50 plans cache
    if len(PLAN_CACHE) > 50:
        oldest = list(PLAN_CACHE.keys())[0]
        del PLAN_CACHE[oldest]
```

**Optimization 4: LangGraph Persistence (Optional)**
```python
# langgraph_brain.py mein — SQLite checkpointer for state persistence
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("kypzer_state.db")
compiled_graph = graph.compile(checkpointer=checkpointer)

# Thread-based execution — commands ka ek thread_id
result = compiled_graph.invoke(initial_state, config={"configurable": {"thread_id": "kypzer_main"}})
```

---

## 30. TESTING EACH COMPONENT

### 30.1 Test Script — `test_langgraph.py`

```python
# test_langgraph.py
# Har component ko individually test karo

def test_1_state_creation():
    """Test: KypzerState create karna"""
    print("\n=== TEST 1: State Creation ===")
    from kypzer_state import create_initial_state
    state = create_initial_state("Chrome kholo")
    
    assert state["raw_command"] == "Chrome kholo"
    assert state["retry_count"] == 0
    assert state["is_complete"] == False
    print("✅ State creation working")

def test_2_understand_node():
    """Test: UnderstandNode with simple command"""
    print("\n=== TEST 2: UnderstandNode ===")
    from kypzer_state import create_initial_state
    from nodes.understand_node import understand_node
    
    state = create_initial_state("Chrome kholo")
    result = understand_node(state)
    
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['intent_confidence']}")
    print(f"Params: {result['extracted_params']}")
    assert result['intent'] != ""
    print("✅ UnderstandNode working")

def test_3_see_screen_node():
    """Test: SeeScreenNode screenshot"""
    print("\n=== TEST 3: SeeScreenNode ===")
    from kypzer_state import create_initial_state
    from nodes.see_screen_node import see_screen_node
    
    state = create_initial_state("Screen pe kya hai?")
    state["intent"] = "SCREEN_READ"
    state["should_skip_vision"] = False
    
    result = see_screen_node(state)
    print(f"Screen context: {result['screen_context'][:100]}")
    assert result['screen_context'] != ""
    print("✅ SeeScreenNode working")

def test_4_plan_node():
    """Test: PlanNode generates valid plan"""
    print("\n=== TEST 4: PlanNode ===")
    from kypzer_state import create_initial_state
    from nodes.plan_node import plan_node
    
    state = create_initial_state("Chrome kholo")
    state["intent"] = "OPEN_APP"
    state["extracted_params"] = {"app_name": "chrome"}
    state["screen_context"] = "Desktop visible"
    
    result = plan_node(state)
    print(f"Action plan: {result['action_plan']}")
    assert len(result['action_plan']) > 0
    print("✅ PlanNode working")

def test_5_execute_node():
    """Test: ExecuteNode (safe test — screenshot only)"""
    print("\n=== TEST 5: ExecuteNode (Screenshot only) ===")
    from kypzer_state import create_initial_state
    from nodes.execute_node import execute_node
    
    state = create_initial_state("Screenshot lo")
    state["intent"] = "SCREENSHOT"
    state["action_plan"] = [{"step": 1, "action": "SCREENSHOT", "value": None, "wait_after": 0}]
    state["current_step_index"] = 0
    state["total_steps"] = 1
    
    result = execute_node(state)
    print(f"Result: {result['last_action_result']}")
    print("✅ ExecuteNode working")

def test_6_full_pipeline():
    """Test: Complete LangGraph pipeline"""
    print("\n=== TEST 6: Full Pipeline ===")
    from langgraph_brain import process_command
    
    # Safe test command
    result = process_command("Screenshot le lo")
    print(f"Response: {result}")
    assert result != ""
    print("✅ Full pipeline working")

def test_7_error_recovery():
    """Test: Error recovery with fake failure"""
    print("\n=== TEST 7: Error Recovery ===")
    from kypzer_state import create_initial_state
    from nodes.error_recovery_node import error_recovery_node
    
    state = create_initial_state("FakeApp kholo")
    state["intent"] = "OPEN_APP"
    state["action_plan"] = [{"step": 1, "action": "OPEN_APP", "value": "FakeApp123", "wait_after": 0}]
    state["current_step_index"] = 0
    state["current_error"] = "FakeApp123 not found"
    state["retry_count"] = 0
    state["max_retries"] = 3
    state["error_history"] = []
    
    result = error_recovery_node(state)
    print(f"Recovery strategy: {result['recovery_strategy']}")
    print(f"Retry count: {result['retry_count']}")
    assert result['retry_count'] == 1
    print("✅ Error recovery working")

def test_8_autogen_whatsapp_agent():
    """Test: WhatsApp agent (dry run — no actual sending)"""
    print("\n=== TEST 8: WhatsApp Agent ===")
    from agents.whatsapp_agent import whatsapp_tools
    
    tools = {f.__name__: f for f in whatsapp_tools()}
    print(f"Available tools: {list(tools.keys())}")
    assert "send_whatsapp_text" in tools
    assert "search_and_send_file" in tools
    print("✅ WhatsApp agent tools registered")

if __name__ == "__main__":
    print("🧪 Running Kypzer LangGraph + AutoGen Tests")
    print("=" * 50)
    
    tests = [
        test_1_state_creation,
        test_2_understand_node,
        test_3_see_screen_node,
        test_4_plan_node,
        test_5_execute_node,
        test_7_error_recovery,
        test_8_autogen_whatsapp_agent,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    # Full pipeline test last mein
    try:
        test_6_full_pipeline()
        passed += 1
    except Exception as e:
        print(f"❌ Full pipeline FAILED: {e}")
        failed += 1
    
    print(f"Final: {passed+1} total, {failed} failed")
```

---

## 31. INTEGRATION ORDER — STEP BY STEP

### Yeh exact order follow karo — skip mat karna

```
PHASE 1: Foundation (Koi API calls nahi)
─────────────────────────────────────────
Step 1.1: pip install langgraph pyautogen litellm
Step 1.2: kypzer_state.py create karo
Step 1.3: test_1_state_creation() run karo — pass hona chahiye
Step 1.4: nodes/ folder create karo with __init__.py
Step 1.5: agents/ folder create karo with __init__.py

PHASE 2: Simple Nodes (Koi screen/API interaction nahi)
─────────────────────────────────────────────────────────
Step 2.1: nodes/understand_node.py create karo
          (Pehle hardcoded response se — Gemini integration baad mein)
Step 2.2: nodes/plan_node.py create karo
          (Rule-based plans only pehle — no Gemini)
Step 2.3: nodes/respond_node.py create karo
          (tts.py call karo)
Step 2.4: Inhe test karo individually

PHASE 3: Screen Nodes
──────────────────────
Step 3.1: vision_helpers.py create karo
Step 3.2: nodes/see_screen_node.py create karo
          (screen_ai.py import karo)
Step 3.3: nodes/verify_node.py create karo
          (simple window title check se shuru karo)
Step 3.4: Test on "Chrome kholo" command

PHASE 4: Execute Node
──────────────────────
Step 4.1: nodes/execute_node.py create karo
          (ACTION_MAP mein actions.py functions map karo)
Step 4.2: nodes/error_recovery_node.py create karo
Step 4.3: test_execute_node() run karo

PHASE 5: Graph Assembly
────────────────────────
Step 5.1: langgraph_brain.py create karo
          (build_kypzer_graph() function)
Step 5.2: test_full_pipeline() run karo
Step 5.3: brain_wrapper.py create karo
          (LangGraph + fallback to classic brain)

PHASE 6: main.py Integration
──────────────────────────────
Step 6.1: main.py mein import brain_wrapper add karo
Step 6.2: brain.process() call ko brain_wrapper.smart_process() se replace karo
Step 6.3: Test: Simple commands still fast? (Volume, brightness)
Step 6.4: Test: Complex command LangGraph se process hota hai?
Step 6.5: Test: LangGraph fail hone pe fallback kaam karta hai?

PHASE 7: AutoGen Agents
────────────────────────
Step 7.1: agents/memory_agent.py create karo (simplest)
Step 7.2: agents/action_agent.py create karo
Step 7.3: agents/vision_agent.py create karo
Step 7.4: agents/whatsapp_agent.py create karo
Step 7.5: Har agent individually test karo

PHASE 8: GroupChat + Bridge
─────────────────────────────
Step 8.1: agents/group_chat.py create karo
Step 8.2: agent_bridge.py create karo
Step 8.3: execute_node.py mein multi_agent_needed check add karo
Step 8.4: Test: "Papa ko resume bhejo" — WhatsApp + file search

PHASE 9: Full Integration Test
────────────────────────────────
Step 9.1: test_langgraph.py run karo — sab pass?
Step 9.2: Real voice input test karo
Step 9.3: Monitor logs, errors fix karo
Step 9.4: Performance check — latency acceptable?

PHASE 10: Memory Enhancement
──────────────────────────────
Step 10.1: memory.py mein new functions add karo
Step 10.2: UnderstandNode mein memory context integration
Step 10.3: RespondNode mein session save
Step 10.4: Test: Cross-command context working?
```

---

## 32. COMPLETE DATA FLOW — ALL SCENARIOS

### Scenario A: "Chrome kholo" (Simple App Open)

```
1. main.py: voice receive kiya → "Chrome kholo"
2. main.py: fast routes check → NO MATCH
3. main.py: intent.py check → NO MATCH (OPEN_APP intent.py mein nahi)
4. main.py: brain_wrapper.smart_process("Chrome kholo")

5. LANGGRAPH START:
   create_initial_state("Chrome kholo")
   
6. UnderstandNode:
   Gemini → intent="OPEN_APP", params={app_name:"chrome"}, confidence=0.95
   should_skip_vision=False (app opening verify karna hai)
   → NEXT: see_screen_node
   
7. SeeScreenNode:
   screenshot liya → "Desktop visible, no Chrome window open"
   ui_elements_found: [taskbar, desktop_icons]
   → NEXT: plan_node
   
8. PlanNode:
   Rule-based: OPEN_APP → 2-step plan
   plan = [
     {step:1, action:"OPEN_APP", value:"chrome", wait_after:2.0},
     {step:2, action:"VERIFY_APP_OPEN", value:"chrome", wait_after:0}
   ]
   needs_multi_agent = False (simple task)
   → NEXT: execute_node
   
9. ExecuteNode (Step 1):
   ACTION_MAP["OPEN_APP"]("chrome") → actions.open_app("chrome")
   Chrome opens...
   last_action_result = "success"
   → NEXT: verify_node
   
10. VerifyNode (Step 1):
    Strategy: "window_check"
    pygetwindow.getWindowsWithTitle("Chrome") → found!
    verification_result = "confirmed"
    current_step_index++ (1 → 2 is out of range? No, still step 2)
    Actually: current_step_index stays at 0 for verify,
              then routes to execute for step 2
    → NEXT: execute_node (step 2)
    
11. ExecuteNode (Step 2):
    "VERIFY_APP_OPEN" → check window → found → mark success
    all steps done (step 2 was last)
    → NEXT: verify_node
    
12. VerifyNode (Step 2):
    "skipped" (verify step itself)
    current_step_index = 2, total_steps = 2, done
    → NEXT: respond_node
    
13. RespondNode:
    response_text = "Chrome khol diya!"
    tts.speak_async("Chrome khol diya!")
    memory.add_to_memory("Chrome kholo", "Chrome khol diya!")
    is_complete = True
    
TOTAL TIME: ~3-4 seconds
(Abhi brain.py se: ~2-3s, but without verify)
```

### Scenario B: "Volume badha" (Fast Path — LangGraph NAHI chalega)

```
1. main.py: voice → "volume badha"
2. main.py: fast routes check → NO MATCH
3. main.py: intent.py → MATCH! VOLUME_UP pattern
4. intent.py returns: {"action": "VOLUME_UP", "say": "वॉल्यूम बढ़ा दिया!"}
5. actions.change_volume(+10)
6. tts.speak("वॉल्यूम बढ़ा दिया!")

LANGGRAPH NEVER CALLED.
TOTAL TIME: <0.5s ✅
```

### Scenario C: "Papa ko resume bhejo" (Complex Multi-Step)

```
1. main.py: voice → "papa ko resume bhejo"
2. fast routes: _fast_whatsapp_route() → MATCH!
   Returns: {action: "SEND_WHATSAPP_FILE_SMART", value: "papa ko resume bhejo"}
   
   WAIT — Abhi fast route directly handler.py call karta hai.
   
   CHOICE: Do we bypass LangGraph here?
   ANSWER: YES for fast route! Fast routes UNCHANGED.
   
   brain_wrapper.smart_process() NAHI CALL HOGA.
   Direct whatsapp handler call hoga.
   
   BUT — handler.py ke andar hi error recovery nahi hai.
   
   BETTER APPROACH: 
   brain_wrapper mein check karo:
   Agar command fast_whatsapp route se aaya aur fail hua →
   Tab LangGraph ke through try karo with full agent support.
   
   Agar NO ERROR → fast path complete as before ✅

ALTERNATIVE — Agar directly LangGraph se chalana chahein:
1. brain_wrapper.smart_process("papa ko resume bhejo")
2. UnderstandNode: intent="WHATSAPP_FILE_SMART", contact="papa", keyword="resume"
3. SeeScreenNode: "Desktop visible"
4. PlanNode: 7-step WhatsApp file plan, needs_multi_agent=True
5. ExecuteNode: agent_bridge.execute_with_multi_agent(state)
   
   AutoGen GroupChat start:
   Orchestrator: "WhatsAppAgent, papa ko resume bhejo"
   WhatsAppAgent: 
     → file_search.search_files("resume") → found: resume.pdf, resume_old.pdf
     → tts.speak("2 files mili: resume.pdf, resume_old.pdf")
     → mic.listen() → "pehli"
     → clipboard.copy(resume.pdf)
     → wa_controller.open_whatsapp_chat("papa")
     → wa_controller.paste_and_send()
   WhatsAppAgent: "TASK_COMPLETE: resume.pdf sent to papa"
   Orchestrator: "TASK_COMPLETE"
   
6. VerifyNode: vision_ai check → "✓ sent in WhatsApp"
7. RespondNode: "resume.pdf bhej diya papa ko!"

TOTAL TIME: ~15-20s (same as before, but WITH verification + retry if failed)
```

### Scenario D: "Screen pe error hai, samjhao" (Screen AI Multi-Agent)

```
1. brain_wrapper.smart_process("screen pe error hai samjhao")
2. UnderstandNode: intent="SCREEN_READ", confidence=0.9
   should_skip_vision=False
3. SeeScreenNode: screenshot → "Python traceback visible, ModuleNotFoundError: numpy"
4. PlanNode: 
   intent = SCREEN_READ → simple description dena hai
   plan = [{step:1, action:"SCREEN_READ", value:"explain error", wait_after:0}]
5. ExecuteNode:
   "SCREEN_READ" → screen_ai.analyze_screen("Explain the error on screen")
   → "ModuleNotFoundError: No module named 'numpy'. 
      Fix: pip install numpy"
6. VerifyNode: "skipped" (read action, no state change)
7. RespondNode: 
   "Screen pe NumPy module nahi mila error hai. 
    Fix ke liye terminal mein 'pip install numpy' run karo!"
   tts.speak(response)
```

### Scenario E: LangGraph Failure → Fallback

```
1. brain_wrapper.smart_process("Kuch complex command")
2. LangGraph start hua
3. UnderstandNode: Gemini API timeout! Exception thrown.
4. langgraph_brain.py try-except catches it
5. Fallback: classic_brain.process("Kuch complex command")
6. Old Gemini call → response milti hai
7. User ko response milta hai — seamless fallback ✅

Log mein print hoga: "[LangGraph Error] Gemini timeout — falling back to brain.py"
```

---

## 33. NEW DEPENDENCIES — REQUIREMENTS.TXT UPDATE

### 33.1 Add to requirements.txt

```txt
# ─────────────────────────────────────────────
# EXISTING DEPENDENCIES (mat change karo)
# ─────────────────────────────────────────────
google-generativeai
groq
pyautogui
pycaw
keyboard
pyperclip
speech_recognition
pyaudio
pygame
requests
chromadb
pillow
mss
pygetwindow
gtts
python-dotenv
AppOpener

# ─────────────────────────────────────────────
# NEW — LANGGRAPH DEPENDENCIES
# ─────────────────────────────────────────────
langgraph>=0.2.0          # Main LangGraph package
langgraph-checkpoint-sqlite  # State persistence (optional)
langchain-core>=0.2.0     # LangChain core (LangGraph depends on it)

# ─────────────────────────────────────────────
# NEW — AUTOGEN DEPENDENCIES  
# ─────────────────────────────────────────────
pyautogen>=0.2.0          # AutoGen framework
litellm>=1.0.0            # LLM provider abstraction (AutoGen uses this)

# ─────────────────────────────────────────────
# UTILITY ADDITIONS
# ─────────────────────────────────────────────
typing-extensions>=4.0.0  # TypedDict improvements
```

### 33.2 Installation Commands

```bash
# LangGraph install
pip install langgraph langchain-core

# AutoGen install (choose one):
pip install pyautogen[gemini]    # Gemini support ke saath
# ya
pip install pyautogen            # Basic

# LiteLLM (AutoGen ke liye)
pip install litellm

# Optional — State persistence
pip install langgraph-checkpoint-sqlite
```

### 33.3 Verify Installation

```python
# verify_install.py — run karo after install

def verify():
    errors = []
    
    try:
        import langgraph
        print(f"✅ LangGraph: {langgraph.__version__}")
    except ImportError as e:
        errors.append(f"❌ LangGraph: {e}")
    
    try:
        import autogen
        print(f"✅ AutoGen: {autogen.__version__}")
    except ImportError as e:
        errors.append(f"❌ AutoGen: {e}")
    
    try:
        import litellm
        print(f"✅ LiteLLM: {litellm.__version__}")
    except ImportError as e:
        errors.append(f"❌ LiteLLM: {e}")
    
    try:
        from langgraph.graph import StateGraph
        print("✅ StateGraph importable")
    except ImportError as e:
        errors.append(f"❌ StateGraph: {e}")
    
    if errors:
        print("\nFix these first:")
        for e in errors:
            print(e)
    else:
        print("\n✅ All dependencies ready!")

verify()
```

---

## 34. CONFIGURATION — NEW ENV.ENV KEYS

### 34.1 Existing Keys — Mat Change Karo

```env
GEMINI_API_KEY=your_key_here
GEMINI_API_KEY_2=your_key_2
GEMINI_API_KEY_3=your_key_3
GEMINI_API_KEY_4=your_key_4
INWORLD_API_KEY=your_inworld_key
GROQ_API_KEY=your_groq_key
```

### 34.2 New Keys to Add

```env
# ─────────────────────────────────────────────
# LANGGRAPH CONFIGURATION
# ─────────────────────────────────────────────

# LangGraph use karna hai ya classic brain? (true/false)
LANGGRAPH_ENABLED=true

# Complex commands ke liye confidence threshold
# Is se kam confidence → LangGraph skip, classic brain use
LANGGRAPH_CONFIDENCE_THRESHOLD=0.6

# Maximum retries per action
LANGGRAPH_MAX_RETRIES=3

# Verification skip karna hai? (true=faster, false=more reliable)
LANGGRAPH_SKIP_VERIFY=false

# State persistence enable karna hai? (SQLite)
LANGGRAPH_PERSIST_STATE=false
LANGGRAPH_STATE_DB_PATH=kypzer_state.db

# ─────────────────────────────────────────────
# AUTOGEN CONFIGURATION
# ─────────────────────────────────────────────

# AutoGen GroupChat enable karna hai?
AUTOGEN_ENABLED=true

# Multi-agent task ke liye minimum steps threshold
# Is se kam steps = single agent, zyada = GroupChat
AUTOGEN_MULTI_AGENT_THRESHOLD=5

# AutoGen conversation max rounds
AUTOGEN_MAX_ROUNDS=20

# Model for AutoGen agents
AUTOGEN_MODEL=gemini-2.0-flash

# ─────────────────────────────────────────────
# PERFORMANCE TUNING
# ─────────────────────────────────────────────

# Screenshot quality for Vision AI (1-100)
VISION_SCREENSHOT_QUALITY=85

# Max width for screenshots (pixels)
VISION_MAX_WIDTH=1366

# Verification timeout (seconds)
VERIFY_TIMEOUT=5

# Response language preference
DEFAULT_RESPONSE_LANGUAGE=hinglish
```

### 34.3 Config Loader — `config.py`

```python
# config.py (project root mein)
import os
from dotenv import load_dotenv

load_dotenv("env.env")

class KypzerConfig:
    # Gemini Keys
    GEMINI_KEYS = [
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3"),
        os.getenv("GEMINI_API_KEY_4"),
    ]
    GEMINI_KEYS = [k for k in GEMINI_KEYS if k]  # None remove karo
    
    # Other APIs
    INWORLD_KEY = os.getenv("INWORLD_API_KEY")
    GROQ_KEY = os.getenv("GROQ_API_KEY")
    
    # LangGraph
    LANGGRAPH_ENABLED = os.getenv("LANGGRAPH_ENABLED", "true").lower() == "true"
    LANGGRAPH_MAX_RETRIES = int(os.getenv("LANGGRAPH_MAX_RETRIES", "3"))
    LANGGRAPH_SKIP_VERIFY = os.getenv("LANGGRAPH_SKIP_VERIFY", "false").lower() == "true"
    
    # AutoGen
    AUTOGEN_ENABLED = os.getenv("AUTOGEN_ENABLED", "true").lower() == "true"
    AUTOGEN_MODEL = os.getenv("AUTOGEN_MODEL", "gemini-2.0-flash")
    AUTOGEN_MAX_ROUNDS = int(os.getenv("AUTOGEN_MAX_ROUNDS", "20"))
    
    # Vision
    VISION_QUALITY = int(os.getenv("VISION_SCREENSHOT_QUALITY", "85"))
    VISION_MAX_WIDTH = int(os.getenv("VISION_MAX_WIDTH", "1366"))
    
    @classmethod
    def get_active_gemini_key(cls) -> str:
        """Round-robin key rotation (existing logic)"""
        # Existing key rotation logic use karo
        return cls.GEMINI_KEYS[0] if cls.GEMINI_KEYS else None

config = KypzerConfig()
```

---

## 35. WHAT EACH OLD FILE BECOMES

### Final Summary Table

| Old File | New Status | Why | What Changed |
|----------|-----------|-----|-------------|
| `main.py` | MOSTLY UNCHANGED | Fast path rakhna hai | 1 line: brain → brain_wrapper |
| `brain.py` | KEPT as fallback | Fallback zaroor chahiye | Nothing |
| `actions.py` | UNTOUCHED | Works as tool library | Nothing |
| `intent.py` | UNTOUCHED | Fast offline path | Nothing |
| `screen_ai.py` | UNTOUCHED | Wrapped externally | Nothing |
| `memory.py` | ENHANCED | New helper methods | Added 3 new functions at bottom |
| `mic.py` | UNTOUCHED | No changes needed | Nothing |
| `stt.py` | UNTOUCHED | No changes needed | Nothing |
| `tts.py` | UNTOUCHED | Called by respond_node | Nothing |
| `whatsapp_module/` | UNTOUCHED | Wrapped by agent | Nothing |
| `grabifier.py` | UNTOUCHED | Independent tool | Nothing |
| `env.env` | EXTENDED | New config keys | Added ~10 new keys |
| `requirements.txt` | EXTENDED | New packages | Added langgraph, pyautogen |

### New Files Created

| New File | Purpose |
|----------|---------|
| `kypzer_state.py` | Central state TypedDict |
| `langgraph_brain.py` | LangGraph graph assembly + entry point |
| `brain_wrapper.py` | Smart routing: LangGraph vs classic |
| `agent_bridge.py` | LangGraph → AutoGen bridge |
| `vision_helpers.py` | screen_ai.py wrapper utilities |
| `config.py` | Centralized config loader |
| `test_langgraph.py` | Component tests |
| `nodes/__init__.py` | Module init |
| `nodes/understand_node.py` | Command understanding |
| `nodes/see_screen_node.py` | Screen context |
| `nodes/plan_node.py` | Action planning |
| `nodes/execute_node.py` | Action execution |
| `nodes/verify_node.py` | Action verification |
| `nodes/respond_node.py` | User response |
| `nodes/error_recovery_node.py` | Error handling + retry |
| `agents/__init__.py` | Module init |
| `agents/orchestrator_agent.py` | Boss AutoGen agent |
| `agents/vision_agent.py` | Screen specialist |
| `agents/action_agent.py` | Action specialist |
| `agents/whatsapp_agent.py` | WhatsApp specialist |
| `agents/memory_agent.py` | Memory specialist |
| `agents/group_chat.py` | Multi-agent coordination |

---

## FINAL NOTES FOR IDE AI

> **HOW TO IMPLEMENT THIS DOCUMENT:**
>
> 1. Read this entire document first before writing any code
> 2. Create files in the ORDER specified in Section 31
> 3. NEVER delete or modify: main.py (except 1 line), brain.py, actions.py, intent.py, screen_ai.py, mic.py, stt.py, tts.py, grabifier.py, or anything in whatsapp_module/
> 4. After each Phase (1-10) in Section 31, run the corresponding test before moving forward
> 5. If a test fails, fix it before continuing
> 6. The fast path (intent.py + fast routes in main.py) must remain <0.5s after implementation
> 7. LangGraph must gracefully fall back to brain.py on any exception
> 8. When in doubt about existing function names in screen_ai.py or memory.py, READ those files first
> 9. All new code uses the config.py KypzerConfig class for API keys
> 10. Logs: add print("[NodeName] message") in each node for debugging

---

*Document generated for Kypzer AI — LangGraph + AutoGen Integration*
*Version: 1.0 | Date: June 9, 2026*
*Total Scope: 22 new files, 2 enhanced files, 1 minimal change*
