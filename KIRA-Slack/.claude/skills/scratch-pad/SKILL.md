---
name: scratch-pad
description: |
  Markdown-based working memory for complex tasks. Use when: 5+ tool calls needed, researching multiple sources, 
  analyzing/comparing items, multi-step workflows. Record process → Reference for response → Delete after use
---

# Scratch Pad - Markdown-Based Task Memory

Simple markdown file for tracking progress during complex tasks. All content is directly written to a `.md` file for immediate use.

## Quick Start

```bash
# Initialize scratch pad
python scripts/scratch_pad.py init "Task Name"

# Add content
python scripts/scratch_pad.py append "Finding: The analysis shows..."

# Log tool calls
python scripts/scratch_pad.py log-tool "web_search" '{"query": "AI trends"}' "Found 10 results"

# Read current content
python scripts/scratch_pad.py read
```

## Core Commands

### Basic Operations

```bash
# Start new task
python scripts/scratch_pad.py --file /path/to/scratch.md init "Task Name"

# Add any content
python scripts/scratch_pad.py append "Content to add..."

# Add section header
python scripts/scratch_pad.py section "Research Findings"

# Read entire pad
python scripts/scratch_pad.py read
```

### Structured Logging

```bash
# Log tool execution
python scripts/scratch_pad.py log-tool "tool_name" '{"param": "value"}' "result text"

# Add finding
python scripts/scratch_pad.py finding "Important discovery" --category "Analysis"  

# Add checkpoint
python scripts/scratch_pad.py checkpoint "Phase 1 Complete"

# Add TODO
python scripts/scratch_pad.py todo "Follow up on this"
python scripts/scratch_pad.py todo "Completed task" --done

# Mark complete
python scripts/scratch_pad.py complete
```

## When to Use

**ALWAYS use for:**
- Tasks with 5+ tool calls
- Multi-source research ("조사해줘")
- Comparative analysis ("비교해줘")
- Information synthesis ("정리해줘")
- Step-by-step processing

## Integration Pattern

```bash
# 1. Initialize at task start
SCRATCH_FILE="FILESYSTEM_BASE_DIR/files/{channel_id}/tmp/scratch_{timestamp}.md"
python scripts/scratch_pad.py --file $SCRATCH_FILE init "User request summary"

# 2. Log each tool call
python scripts/scratch_pad.py --file $SCRATCH_FILE log-tool "mcp__perplexity__search" '{"query": "..."}'
# Execute tool...
python scripts/scratch_pad.py --file $SCRATCH_FILE append "Result: Found X relevant items"

# 3. Add findings
python scripts/scratch_pad.py --file $SCRATCH_FILE finding "Key insight from research"

# 4. Read content for reference (DO NOT include raw content in response)
CONTENT=$(python scripts/scratch_pad.py --file $SCRATCH_FILE read)
# Use $CONTENT as reference to write organized response in mcp__slack__answer

# 5. Clean up (REQUIRED)
rm $SCRATCH_FILE
```

**Important**: 
- The scratch pad is for YOUR reference only
- DO NOT copy/paste the raw markdown into responses
- USE it to organize and write a proper answer
- ALWAYS delete the scratch file after use

## Output Format

The markdown file is structured for easy reading:

```markdown
# 📋 Task Name

**Created:** 2025-11-05 10:00:00
**Status:** 🔄 In Progress

---

## 📝 Task Overview
Task: Research competitor products
Started: 2025-11-05 10:00:00

---

## Research Findings (10:05:23)

[10:05:30] Found 3 main competitors...

### 🔧 [10:06:15] Tool: web_search

**Parameters:**
```json
{
  "query": "competitor analysis"
}
```

**Result:**
```
Found 10 relevant results
```

---

### ✅ Checkpoint: Initial Research Complete
**Time:** 10:15:00
Gathered basic information on all competitors

---
```

## Best Practices

1. **Use descriptive section headers** - Makes content easy to navigate
2. **Log tools immediately** - Capture parameters before execution
3. **Add findings as you go** - Don't wait until the end
4. **Use checkpoints** - Mark major milestones
5. **Reference, don't copy** - Use scratch pad as reference for organized response
6. **Always clean up** - Delete scratch files after task completion
7. **Keep it concise** - Focus on key information for YOUR reference

## Module Usage

```python
from scripts.scratch_pad import ScratchPadManager

# Initialize
manager = ScratchPadManager('/tmp/task.md')
manager.init("Complex Analysis Task")

# Add content
manager.add_section("Research Phase")
manager.append("Starting research on topic X...")

# Log tool
manager.log_tool("web_search", {"query": "topic X"}, "10 results found")

# Add finding
manager.add_finding("Topic X is growing 50% annually", "Market Trends")

# Read content
content = manager.read()

# Mark complete
manager.complete()
```

## File Management

- **Location**: Always in `FILESYSTEM_BASE_DIR/files/{channel_id}/tmp/`
- **Naming**: `scratch_{timestamp}.md` or `scratch_{task_id}.md`
- **Cleanup**: Delete after task completion
- **Size limit**: Keep under 1MB for performance

## Why Markdown?

- ✅ Human-readable format
- ✅ No JSON parsing overhead
- ✅ Direct append operations
- ✅ Easy to include in responses
- ✅ Can be viewed/edited manually
- ✅ Natural structure for documentation
