#!/usr/bin/env python3
"""
Search through memory files for keywords, tags, or metadata.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import re

class MemorySearch:
    """Search through employee memory."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
    
    def extract_metadata(self, content: str) -> Dict:
        """Extract YAML frontmatter metadata."""
        if not content.startswith('---'):
            return {}
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}
        
        metadata = {}
        for line in parts[1].strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        return metadata
    
    def search_content(self, query: str, case_sensitive: bool = False) -> List[Tuple[str, str, List[str]]]:
        """
        Search for query in file contents.
        Returns list of (directory, filename, matching_lines).
        """
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for file_path in self.base_path.rglob('*.md'):
            if file_path.name == 'index.md':
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if not case_sensitive:
                    search_content = content.lower()
                else:
                    search_content = content
                
                if query in search_content:
                    # Extract matching lines
                    matching_lines = []
                    for i, line in enumerate(content.split('\n'), 1):
                        search_line = line if case_sensitive else line.lower()
                        if query in search_line:
                            matching_lines.append(f"L{i}: {line.strip()}")
                    
                    rel_path = file_path.relative_to(self.base_path)
                    directory = str(rel_path.parent)
                    filename = file_path.name
                    results.append((directory, filename, matching_lines))
            
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        
        return results
    
    def search_by_tag(self, tag: str) -> List[Tuple[str, str, Dict]]:
        """
        Search for files with a specific tag.
        Returns list of (directory, filename, metadata).
        """
        results = []
        
        for file_path in self.base_path.rglob('*.md'):
            if file_path.name == 'index.md':
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                metadata = self.extract_metadata(content)
                
                # Check if tag exists in metadata
                if 'tags' in metadata:
                    tags_str = metadata['tags'].lower()
                    if tag.lower() in tags_str:
                        rel_path = file_path.relative_to(self.base_path)
                        directory = str(rel_path.parent)
                        filename = file_path.name
                        results.append((directory, filename, metadata))
            
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        
        return results
    
    def search_by_category(self, category: str) -> List[Tuple[str, str]]:
        """
        Search for files in a specific category/directory.
        Returns list of (directory, filename).
        """
        results = []
        category_path = self.base_path / category
        
        if not category_path.exists():
            return results
        
        for file_path in category_path.rglob('*.md'):
            if file_path.name == 'index.md':
                continue
            
            rel_path = file_path.relative_to(self.base_path)
            directory = str(rel_path.parent)
            filename = file_path.name
            results.append((directory, filename))
        
        return results
    
    def print_results(self, results: List, search_type: str) -> None:
        """Pretty print search results."""
        if not results:
            print("\n❌ No results found.")
            return
        
        print(f"\n✅ Found {len(results)} result(s):\n")
        
        for i, result in enumerate(results, 1):
            if search_type == 'content':
                directory, filename, matching_lines = result
                print(f"{i}. 📄 {directory}/{filename}")
                for line in matching_lines[:3]:  # Show first 3 matches
                    print(f"   {line}")
                if len(matching_lines) > 3:
                    print(f"   ... and {len(matching_lines) - 3} more matches")
                print()
            
            elif search_type == 'tag':
                directory, filename, metadata = result
                print(f"{i}. 📄 {directory}/{filename}")
                if 'title' in metadata:
                    print(f"   Title: {metadata['title']}")
                if 'tags' in metadata:
                    print(f"   Tags: {metadata['tags']}")
                print()
            
            elif search_type == 'category':
                directory, filename = result
                print(f"{i}. 📄 {directory}/{filename}")

def main():
    """Main CLI interface."""
    if len(sys.argv) < 3:
        print("Usage: python search_memory.py <memory_path> <search_type> <query>")
        print("\nSearch Types:")
        print("  content <query>     - Search in file contents")
        print("  tag <tag>           - Search by tag")
        print("  category <category> - List files in category")
        print("\nExamples:")
        print("  python search_memory.py /memory content '프로젝트'")
        print("  python search_memory.py /memory tag urgent")
        print("  python search_memory.py /memory category projects")
        sys.exit(1)
    
    memory_path = sys.argv[1]
    search_type = sys.argv[2].lower()
    query = sys.argv[3] if len(sys.argv) > 3 else ""
    
    searcher = MemorySearch(memory_path)
    
    if search_type == 'content':
        results = searcher.search_content(query)
        searcher.print_results(results, 'content')
    
    elif search_type == 'tag':
        results = searcher.search_by_tag(query)
        searcher.print_results(results, 'tag')
    
    elif search_type == 'category':
        results = searcher.search_by_category(query)
        searcher.print_results(results, 'category')
    
    else:
        print(f"Error: Unknown search type '{search_type}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
