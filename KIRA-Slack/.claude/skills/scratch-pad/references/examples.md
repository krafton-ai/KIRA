# Scratch Pad Usage Examples

## Basic Research Task

```bash
# Initialize
SCRATCH="/tmp/scratch_research.md"
python scripts/scratch_pad.py --file $SCRATCH init "Competitor Analysis"

# Log searches
python scripts/scratch_pad.py --file $SCRATCH log-tool "web_search" '{"query": "competitor A"}' "Found 10 results"
python scripts/scratch_pad.py --file $SCRATCH finding "Competitor A has 30% market share" --category "Market"

python scripts/scratch_pad.py --file $SCRATCH log-tool "web_search" '{"query": "competitor B"}' "Found 8 results"  
python scripts/scratch_pad.py --file $SCRATCH finding "Competitor B focuses on enterprise" --category "Market"

# Add summary
python scripts/scratch_pad.py --file $SCRATCH summary "Three main competitors identified with different market strategies"

# Read for response
python scripts/scratch_pad.py --file $SCRATCH read
```

## Multi-Step Processing

```bash
# Initialize
SCRATCH="/tmp/scratch_process.md"
python scripts/scratch_pad.py --file $SCRATCH init "Data Processing Pipeline"

# Step 1: Load
python scripts/scratch_pad.py --file $SCRATCH section "Step 1: Load Data"
python scripts/scratch_pad.py --file $SCRATCH log-tool "file_read" '{"path": "data.csv"}' "Loaded 1000 rows"
python scripts/scratch_pad.py --file $SCRATCH checkpoint "Data loaded"

# Step 2: Process  
python scripts/scratch_pad.py --file $SCRATCH section "Step 2: Process Data"
python scripts/scratch_pad.py --file $SCRATCH append "Removed 50 duplicate rows"
python scripts/scratch_pad.py --file $SCRATCH append "Applied normalization"
python scripts/scratch_pad.py --file $SCRATCH checkpoint "Processing complete"

# Step 3: Save
python scripts/scratch_pad.py --file $SCRATCH section "Step 3: Save Results"
python scripts/scratch_pad.py --file $SCRATCH log-tool "file_write" '{"path": "output.csv"}' "Saved 950 rows"

# Mark complete
python scripts/scratch_pad.py --file $SCRATCH complete
```

## Document Analysis

```bash
# Initialize
SCRATCH="/tmp/scratch_docs.md"
python scripts/scratch_pad.py --file $SCRATCH init "Confluence Documentation Review"

# Process each page
python scripts/scratch_pad.py --file $SCRATCH section "Main Page Analysis"
python scripts/scratch_pad.py --file $SCRATCH log-tool "confluence_read" '{"page_id": "123"}' "Read main page"
python scripts/scratch_pad.py --file $SCRATCH finding "Main page covers project overview"

python scripts/scratch_pad.py --file $SCRATCH section "Child Pages"
python scripts/scratch_pad.py --file $SCRATCH todo "Review technical specs page"
python scripts/scratch_pad.py --file $SCRATCH todo "Check API documentation" 
python scripts/scratch_pad.py --file $SCRATCH todo "Update outdated examples" --done

# Summary
python scripts/scratch_pad.py --file $SCRATCH summary "Documentation is mostly complete but needs updates in 3 areas"
```

## Quick Patterns

### Finding Pattern
```bash
python scripts/scratch_pad.py --file $SCRATCH finding "Discovery text" --category "Category"
```

### Tool Logging Pattern
```bash
# Before execution
python scripts/scratch_pad.py --file $SCRATCH log-tool "tool_name" '{"params": "value"}' ""
# After execution  
python scripts/scratch_pad.py --file $SCRATCH append "Result: Success with X items"
```

### Section Organization
```bash
python scripts/scratch_pad.py --file $SCRATCH section "Phase 1: Research"
# ... add content ...
python scripts/scratch_pad.py --file $SCRATCH section "Phase 2: Analysis"  
# ... add content ...
python scripts/scratch_pad.py --file $SCRATCH section "Phase 3: Conclusions"
```
