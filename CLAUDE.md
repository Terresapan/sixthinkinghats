# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Six Thinking Hats** is an AI-powered decision-making web application that implements Edward de Bono's Six Thinking Hats methodology. It provides multi-perspective analysis using different AI "thinking hats" (White, Red, Yellow, Black, Green, Blue) that analyze questions from distinct viewpoints, using a phased sequential architecture with intelligent search orchestration.

## 🏗️ Architecture

### Core Architecture Pattern
- **Phased Sequential System**: 4-phase workflow with intelligent query analysis
  - Phase 0: Query analysis & search orchestration (Manager Agent)
  - Phase 1: Parallel execution (White, Red, Yellow, Black hats)
  - Phase 2: Sequential aggregation & Green Hat (creativity)
  - Phase 3: Final synthesis with Blue Hat
- **Multi-Agent System**: 6 specialized thinking hat agents + Manager Agent
- **Cost-Optimized**: Intelligent search budget management (max 4 searches per query)
- **LangGraph-Powered**: State management and workflow orchestration

### Key Technologies
- **Language**: Python 3.11+
- **Web UI**: Streamlit
- **AI Framework**: LangChain + LangGraph
- **LLM Provider**: OpenAI (GPT-5-mini - currently active)
- **Web Search**: Tavily Search API
- **Observability**: LangSmith

### Directory Structure
```
sixthinkinghats/
├── streamlit_app.py             # Web UI entry point
├── requirements.txt             # Python dependencies
│
├── .streamlit/                  # Streamlit configuration
│   ├── config.toml             # Dark theme configuration
│   └── secrets.toml            # API keys (not tracked)
│
├── agents/                      # Thinking Hat Agents
│   ├── base_agent.py           # Abstract base class
│   ├── thinking_hat_agents.py  # 6 specialized agents
│   └── manager_agent.py        # Query analyzer & search allocator
│
├── services/                    # Search & Orchestration
│   ├── search_apis.py          # Search API providers (Tavily)
│   ├── search_orchestrator.py  # Original search orchestrator
│   └── phased_search_orchestrator.py  # Enhanced phased search manager
│
└── graph/                       # Workflow Orchestration
    └── phased_workflow_graph.py # LangGraph phased workflow
```

### Processing Phases (Sequential Workflow)
1. **Phase 0: Analysis & Search** (Manager Agent + Search Orchestrator)
   - Analyzes query complexity and topic
   - Allocates search budget (max 4 searches)
   - Executes initial search wave
2. **Phase 1: Parallel Execution** (White, Red, Yellow, Black hats)
   - All 4 hats run concurrently with search contexts
   - Independent analysis from each perspective
3. **Phase 2: Sequential Aggregation** (Aggregator + Green Hat)
   - Aggregates parallel results into context
   - Green Hat processes with full aggregated context
4. **Phase 3: Final Synthesis** (Blue Hat)
   - Synthesizes all perspectives
   - Provides comprehensive summary and recommendations

## 🚀 Common Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application

**Web Interface**:
```bash
streamlit run streamlit_app.py
```

**Test the Implementation**:
```bash
python test_phased_workflow.py
```

### Search Integration
- **Intelligent Budget Allocation**: Manager Agent allocates max 4 searches based on query analysis
- **Query Analysis**: Determines complexity (simple/moderate/complex) and topic domain
- **Smart Priorities**: Different hats get contextual searches based on their role:
  - White Hat: Always searches (CRITICAL priority - facts & data)
  - Red Hat: Searches on emotional/social topics (HIGH priority)
  - Yellow Hat: Searches business/opportunity topics (HIGH priority)
  - Black Hat: Searches risk/health/safety topics (HIGH priority)
  - Green Hat: Searches complex problems (MEDIUM priority, if budget allows)
  - Blue Hat: Rarely searches (LOW priority - synthesis focus)
- **Caching**: 1-hour TTL with duplicate detection
- **Multiple Search Waves**: Initial wave (Phase 0) + optional sequential searches

## 🔧 Development Notes

### System Prompts
Each thinking hat agent uses specialized system prompts defined in `agents/thinking_hat_agents.py`:
- White: Facts & data analysis
- Red: Emotions & feelings
- Yellow: Optimism & benefits
- Black: Risks & caution
- Green: Creativity & innovation
- Blue: Process & summary

### API Configuration
- **OpenAI API**: Primary LLM provider (GPT-5-mini)
- **Tavily API**: Web search provider
- **LangSmith**: Optional, for tracing and observability
- All API keys configured in `.streamlit/secrets.toml` (not tracked in git)

### Performance Characteristics
- **Total Execution Time**: ~6-10 seconds per query
  - Phase 0 (Analysis): ~1-2s
  - Phase 1 (Parallel): ~3-4s
  - Phase 2 (Aggregation): ~1-2s
  - Phase 3 (Synthesis): ~1-2s
- **Intelligent Caching**: Reduces redundant API calls
- **State Management**: LangGraph ensures consistent state across phases
- **Error Handling**: Each phase has independent error handling
- **Statistics Tracking**: Comprehensive performance metrics

## 📝 Key Files

### Entry Points
- `streamlit_app.py`: Web-based chat interface (only entry point)

### Core Modules
- `agents/manager_agent.py:1`: Analyzes queries, allocates search budget, generates search queries
- `graph/phased_workflow_graph.py:1`: LangGraph workflow orchestrating 4-phase sequential processing
- `services/phased_search_orchestrator.py:1`: Manages search execution across multiple phases with caching
- `agents/base_agent.py:1`: Abstract base class providing search integration and LLM interaction
- `agents/thinking_hat_agents.py:1`: 6 specialized thinking hat agents with process() methods

### Configuration
- `requirements.txt`: Python dependencies
- `.streamlit/config.toml`: Dark theme configuration
- `.streamlit/secrets.toml`: API keys (create from template if missing)

## 🔄 Recent Changes (Current Branch)

**Current modification** (feature/web-search branch):
- **Major Architecture Refactor**: Moved from parallel processing to phased sequential workflow
- **New Components**:
  - Manager Agent for intelligent query analysis
  - Phased Workflow Graph using LangGraph
  - Phased Search Orchestrator for multi-wave search
- **Removed**: CLI interface (main.py), legacy parallel_processor.py
- **Performance**: Structured workflow with explicit phase control
- **Enhanced Search**: Multiple search waves with intelligent budget allocation

## 📚 Additional Documentation

- `PHASED_ARCHITECTURE_QUICKREF.md`: Comprehensive guide to the phased sequential architecture
- `graph.png`: Updated architecture diagram
- The codebase includes extensive inline comments explaining the phased workflow logic and search orchestration

## 🎨 UI Features

**Streamlit App**:
- Chat-based interface
- Displays all 6 hat responses in sequence with avatar indicators
- Phase indicators showing workflow progress
- Real-time streaming of results
- Dark theme (configured in `.streamlit/config.toml`)
- Processing statistics and search budget tracking

## ⚙️ Environment Setup

Required environment variables (via `.streamlit/secrets.toml`):
- `OPENAI_API_KEY`: OpenAI API key for GPT-5-mini
- `TAVILY_API_KEY`: Tavily search API key
- `LANGSMITH_API_KEY`: Optional, for tracing

## 🔍 Troubleshooting

**Import Errors**: Ensure virtual environment is activated and dependencies installed

**Search Not Working**: Verify API keys are configured in `.streamlit/secrets.toml`

**Performance Issues**: Check the processing statistics in the UI; each phase shows execution time

**API Rate Limits**: The system includes intelligent search budget management (max 4 searches/query) and caching to minimize API calls

**Workflow Errors**: Each phase has independent error handling; check the error logs in the processing statistics

**Query Analysis Issues**: The Manager Agent automatically handles query classification; if unexpected results occur, check the rationale in the processing stats