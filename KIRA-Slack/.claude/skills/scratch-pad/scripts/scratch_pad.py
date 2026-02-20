#!/usr/bin/env python3
"""
Scratch Pad Manager (Markdown Version) - Direct markdown file management for long-running tasks

Module usage:
    from scripts.scratch_pad_md import ScratchPadManager
    
    manager = ScratchPadManager('/tmp/scratch.md')
    manager.init("My Task")
    manager.add_section("## Research Findings")
    manager.append("Found 3 key competitors...")
    manager.log_tool("web_search", {"query": "AI trends"}, "Found 10 results")

CLI usage:
    python scripts/scratch_pad_md.py init "My Task" 
    python scripts/scratch_pad_md.py append "## Section Title"
    python scripts/scratch_pad_md.py append "Content to add..."
    python scripts/scratch_pad_md.py log-tool "web_search" '{"query": "test"}' "Result text"
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import argparse
import json

class ScratchPadManager:
    """Markdown-based scratch pad manager"""
    
    def __init__(self, pad_file: str = "/tmp/scratch_pad.md"):
        """Initialize scratch pad manager
        
        Args:
            pad_file: Path to the markdown file
        """
        self.pad_file = Path(pad_file)
        
    def init(self, task_name: str = "Untitled Task") -> Dict[str, Any]:
        """Initialize a new scratch pad with header
        
        Args:
            task_name: Name of the task
            
        Returns:
            Dict with status and message
        """
        # Ensure directory exists
        self.pad_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create initial content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"""# 📋 {task_name}

**Created:** {timestamp}  
**Status:** 🔄 In Progress

---

## 📝 Task Overview
Task: {task_name}
Started: {timestamp}

---

"""
        
        with open(self.pad_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {
            "status": "success",
            "message": f"Initialized scratch pad: {task_name}",
            "file": str(self.pad_file)
        }
    
    def append(self, content: str) -> Dict[str, Any]:
        """Append content to the scratch pad
        
        Args:
            content: Content to append (can include markdown formatting)
            
        Returns:
            Dict with status
        """
        # Add timestamp if content is not a header
        if not content.strip().startswith('#'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            content = f"[{timestamp}] {content}"
        
        # Ensure file exists
        if not self.pad_file.exists():
            self.init()
        
        with open(self.pad_file, 'a', encoding='utf-8') as f:
            f.write(content + "\n\n")
            
        return {"status": "success", "message": "Content appended"}
    
    def add_section(self, title: str) -> Dict[str, Any]:
        """Add a new section with timestamp
        
        Args:
            title: Section title (will be formatted as ## header)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Ensure it's a proper header
        if not title.startswith('#'):
            title = f"## {title}"
            
        content = f"{title} ({timestamp})\n"
        return self.append(content)
    
    def log_tool(self, tool_name: str, parameters: Dict[str, Any], result: str = "") -> Dict[str, Any]:
        """Log a tool call in markdown format
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool result (as string)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format as collapsible detail
        content = f"""### 🔧 [{timestamp}] Tool: {tool_name}

**Parameters:**
```json
{json.dumps(parameters, indent=2, ensure_ascii=False)}
```

**Result:**
```
{result if result else "⏳ Pending..."}
```

---"""
        
        return self.append(content)
    
    def add_finding(self, finding: str, category: str = "General") -> Dict[str, Any]:
        """Add a key finding or observation
        
        Args:
            finding: The finding text
            category: Category of finding
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        content = f"**[{timestamp}] {category}:** {finding}"
        return self.append(content)
    
    def add_checkpoint(self, name: str, description: str = "") -> Dict[str, Any]:
        """Add a checkpoint/milestone marker
        
        Args:
            name: Checkpoint name
            description: Optional description
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        content = f"""---

### ✅ Checkpoint: {name}
**Time:** {timestamp}  
{description}

---"""
        return self.append(content)
    
    def add_summary(self, summary: str) -> Dict[str, Any]:
        """Add a summary section
        
        Args:
            summary: Summary text
        """
        content = f"""## 📊 Summary

{summary}

---"""
        return self.append(content)
    
    def add_todo(self, task: str, completed: bool = False) -> Dict[str, Any]:
        """Add a TODO item
        
        Args:
            task: Task description
            completed: Whether task is completed
        """
        checkbox = "✅" if completed else "⬜"
        content = f"- {checkbox} {task}"
        return self.append(content)
    
    def read(self) -> str:
        """Read the entire scratch pad content"""
        if not self.pad_file.exists():
            return ""
        
        with open(self.pad_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_size(self) -> int:
        """Get file size in bytes"""
        if not self.pad_file.exists():
            return 0
        return self.pad_file.stat().st_size
    
    def complete(self) -> Dict[str, Any]:
        """Mark the task as complete"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"""---

## ✅ Task Complete

**Completed:** {timestamp}  
**Status:** ✅ Complete

---"""
        return self.append(content)


def main():
    """CLI interface for markdown scratch pad"""
    parser = argparse.ArgumentParser(description="Markdown Scratch Pad Manager")
    parser.add_argument("--file", default="/tmp/scratch_pad.md", help="Path to scratch pad file")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new scratch pad")
    init_parser.add_argument("task_name", nargs="?", default="Untitled Task", help="Name of the task")
    
    # Append command
    append_parser = subparsers.add_parser("append", help="Append content")
    append_parser.add_argument("content", help="Content to append")
    
    # Section command
    section_parser = subparsers.add_parser("section", help="Add a new section")
    section_parser.add_argument("title", help="Section title")
    
    # Log tool command
    log_parser = subparsers.add_parser("log-tool", help="Log a tool call")
    log_parser.add_argument("tool_name", help="Tool name")
    log_parser.add_argument("parameters", help="Parameters (JSON)")
    log_parser.add_argument("--result", default="", help="Result")
    
    # Finding command
    finding_parser = subparsers.add_parser("finding", help="Add a finding")
    finding_parser.add_argument("finding", help="Finding text")
    finding_parser.add_argument("--category", default="General", help="Category")
    
    # Checkpoint command
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Add checkpoint")
    checkpoint_parser.add_argument("name", help="Checkpoint name")
    checkpoint_parser.add_argument("--description", default="", help="Description")
    
    # TODO command
    todo_parser = subparsers.add_parser("todo", help="Add TODO item")
    todo_parser.add_argument("task", help="Task description")
    todo_parser.add_argument("--done", action="store_true", help="Mark as done")
    
    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Add summary")
    summary_parser.add_argument("text", help="Summary text")
    
    # Read command
    read_parser = subparsers.add_parser("read", help="Read entire pad")
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark task complete")
    
    args = parser.parse_args()
    
    manager = ScratchPadManager(args.file)
    
    if args.command == "init":
        result = manager.init(args.task_name)
        print(f"✅ {result['message']}")
        
    elif args.command == "append":
        manager.append(args.content)
        print("✅ Content appended")
        
    elif args.command == "section":
        manager.add_section(args.title)
        print(f"✅ Section added: {args.title}")
        
    elif args.command == "log-tool":
        try:
            params = json.loads(args.parameters)
        except:
            params = {"raw": args.parameters}
        manager.log_tool(args.tool_name, params, args.result)
        print(f"✅ Logged tool: {args.tool_name}")
        
    elif args.command == "finding":
        manager.add_finding(args.finding, args.category)
        print(f"✅ Finding added: {args.category}")
        
    elif args.command == "checkpoint":
        manager.add_checkpoint(args.name, args.description)
        print(f"✅ Checkpoint: {args.name}")
        
    elif args.command == "todo":
        manager.add_todo(args.task, args.done)
        print(f"✅ TODO added")
        
    elif args.command == "summary":
        manager.add_summary(args.text)
        print("✅ Summary added")
        
    elif args.command == "read":
        content = manager.read()
        print(content)
        
    elif args.command == "complete":
        manager.complete()
        print("✅ Task marked complete")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
