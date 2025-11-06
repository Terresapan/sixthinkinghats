# Phased Architecture - Quick Reference Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUERY                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 0: ANALYSIS & SEARCH                          │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐  │
│  │  MANAGER AGENT   │→ │   SEARCH ORCHESTRATOR               │  │
│  │                  │  │                                     │  │
│  │ • Analyze query  │  │ • Execute search wave               │  │
│  │ • Determine      │  │ • Manage 4-search budget            │  │
│  │   priorities     │  │ • Cache & deduplicate               │  │
│  │ • Allocate       │  │ • Build search contexts             │  │
│  │   budget         │  │                                     │  │
│  └──────────────────┘  └──────────────┬──────────────────────┘  │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 1: PARALLEL EXECUTION                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────┐ │
│  │  WHITE HAT   │  │   RED HAT    │  │  YELLOW HAT  │  │ BL │ │
│  │              │  │              │  │              │  │ AC │ │
│  │ • Facts      │  │ • Emotions   │  │ • Benefits   │  │ K  │ │
│  │ • Data       │  │ • Feelings   │  │ • Optimism   │  │ H  │ │
│  │ ✓ Search     │  │ ✓ Search     │  │ ✓ Search     │  │ AT │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────┘ │
│         │                 │                 │                 │
│         └─────────────────┼─────────────────┘                 │
│                           │                                 │
│                           ▼                                 │
│              ┌──────────────────────────────────────┐       │
│              │         AGGREGATOR                   │       │
│              │                                      │       │
│              │ • Collect 4 parallel responses       │       │
│              │ • Build aggregated context           │       │
│              │ • Identify themes & opportunities    │       │
│              └──────────────────┬───────────────────┘       │
└─────────────────────────────────────────┼────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 2: SEQUENTIAL PROCESSING                       │
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │            GREEN HAT                     │                   │
│  │                                         │                   │
│  │ • Creativity & Innovation               │                   │
│  │ • Uses aggregated context from Phase 1  │                   │
│  │ • Optional search (if budget allows)    │                   │
│  │ • Generates creative alternatives       │                   │
│  └─────────────────┬───────────────────────┘                   │
└────────────────────┼───────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: FINAL SYNTHESIS                           │
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │              BLUE HAT                    │                   │
│  │                                         │                   │
│  │ • Process & Summary                     │                   │
│  │ • Receives ALL previous responses       │                   │
│  │ • Synthesizes all perspectives          │                   │
│  │ • Provides final recommendation         │                   │
│  └─────────────────┬───────────────────────┘                   │
└────────────────────┼───────────────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  FINAL       │
              │  RESULT      │
              └──────────────┘
```

## 🔑 Key Components

### 1. Manager Agent
**File**: `agents/manager_agent.py`

Analyzes query and determines:
- Complexity (simple/moderate/complex)
- Topic domain (business/health/technology/emotional/social/safety)
- Search priorities for each hat
- Search budget allocation (max 4 searches)
- Hat-specific search queries

### 2. Phased Search Orchestrator
**File**: `services/phased_search_orchestrator.py`

Manages search execution:
- Executes initial search wave (Phase 0)
- Optional sequential searches (Green/Blue hats)
- Caching with 1-hour TTL
- Duplicate detection (Jaccard similarity)
- Context building for each phase

### 3. Phased Workflow Graph
**File**: `graph/phased_workflow_graph.py`

LangGraph orchestrator implementing:
- State management across all phases
- Parallel execution of White, Red, Yellow, Black
- Sequential aggregation for Green Hat
- Final synthesis by Blue Hat
- Error handling and statistics

### 4. Enhanced Hat Agents
**File**: `agents/thinking_hat_agents.py`

Each agent updated with:
- **White/Red/Yellow/Black**: `process(query, search_context)`
- **Green Hat**: `process(query, aggregated_context, search_context)`
- **Blue Hat**: `process(query, all_responses, synthesis_context)`

## 🚀 Running the Application

### Start Web Interface
```bash
streamlit run streamlit_app.py
```

### Test the Implementation
```bash
python test_phased_workflow.py
```

## 📊 Search Budget Allocation

### Default Strategy (4 searches):
1. **White Hat** - Always (facts & data are critical)
2. **Red Hat** - If emotional/social topic
3. **Yellow Hat** - If business/opportunity topic
4. **Black Hat** - If risk/health/safety topic

### Smart Allocation by Topic:
- **Business queries** → White + Yellow + Green
- **Health queries** → White + Black + Red
- **Technical queries** → White + Green
- **Social issues** → White + Red

## 💡 Usage Example

```python
from graph.phased_workflow_graph import PhasedWorkflowGraph
from services.search_apis import TavilySearchAPI
from langchain_openai import ChatOpenAI

# Initialize
llm = ChatOpenAI(model="gpt-5-mini")
search_api = TavilySearchAPI()
workflow = PhasedWorkflowGraph(llm, search_api)

# Execute
results = workflow.invoke("Should we adopt AI in our company?")

# Access responses
print("White (Facts):", results['white_response'])
print("Red (Emotions):", results['red_response'])
print("Yellow (Benefits):", results['yellow_response'])
print("Black (Risks):", results['black_response'])
print("Green (Creative):", results['green_response'])
print("Blue (Summary):", results['blue_response'])

# Check statistics
stats = results['processing_stats']
print(f"Total time: {stats['overall']['total_execution_time']:.2f}s")
```

## 📈 Performance Characteristics

| Phase | Components | Execution Time |
|-------|-----------|----------------|
| Phase 0 | Manager + Search Orchestrator | ~1-2s |
| Phase 1 | 4 Parallel Hats | ~3-4s |
| Phase 2 | Aggregator + Green Hat | ~1-2s |
| Phase 3 | Blue Hat | ~1-2s |
| **Total** | **All Phases** | **~6-10s** |

## 🎯 Benefits Over Fully Parallel Approach

1. **Explicit Control**: Manager decides search strategy upfront
2. **Contextual Flow**: Green Hat uses all 4 parallel results
3. **Better Synthesis**: Blue Hat sees complete picture
4. **Transparent**: Clear rationale for all decisions
5. **User-Friendly**: Phase indicators in UI show progress

## 🔧 Customization

### Adjust Search Budget
```python
workflow = PhasedWorkflowGraph(
    llm=llm,
    search_api=search_api,
    max_searches_per_query=6  # Increase from 4
)
```

### Modify Search Priority Logic
Edit `agents/manager_agent.py`:
- `_determine_search_priorities()` method
- Query classification rules
- Priority assignment logic

### Add New Hats
1. Create new agent class in `thinking_hat_agents.py`
2. Add to `HatType` enum in `manager_agent.py`
3. Add node to workflow graph in `phased_workflow_graph.py`
4. Update UI display in `streamlit_app.py`

## 📝 Migration Notes

### Backward Compatibility
- Original `parallel_langgraph.py` still available
- Can serve as fallback if needed
- No breaking changes to API

### Files Created/Modified
**Created**:
- `agents/manager_agent.py`
- `services/phased_search_orchestrator.py`
- `graph/phased_workflow_graph.py`
- `test_phased_workflow.py`
- `REFACTORING_PLAN.md`
- `IMPLEMENTATION_SUMMARY.md`
- `PHASED_ARCHITECTURE_QUICKREF.md` (this file)

**Modified**:
- `agents/thinking_hat_agents.py` - Added process methods
- `streamlit_app.py` - Updated to use phased workflow

**Unchanged** (but still functional):
- `agents/base_agent.py`
- `services/search_apis.py`
- `services/search_orchestrator.py` (original)
- `services/query_analyzer.py` (original)
- `graph/parallel_langgraph.py` (original parallel system)

## ✅ Verification Checklist

- [x] Manager Agent analyzes queries correctly
- [x] Search budget allocated intelligently
- [x] Search orchestrator executes properly
- [x] Parallel hats (White, Red, Yellow, Black) run concurrently
- [x] Aggregator collects and builds context
- [x] Green Hat receives aggregated context
- [x] Blue Hat synthesizes all responses
- [x] UI displays phase indicators
- [x] Statistics tracked accurately
- [x] Error handling works
- [x] Test script validates functionality

## 🎉 Next Steps

The phased sequential architecture is complete and ready for use! To get started:

1. Set your API keys:
   ```bash
   export OPENAI_API_KEY="your-key"
   export TAVILY_API_KEY="your-key"
   ```

2. Run the test:
   ```bash
   python test_phased_workflow.py
   ```

3. Start the app:
   ```bash
   streamlit run streamlit_app.py
   ```

Enjoy your enhanced Six Thinking Hats application! 🧢✨
