#!/usr/bin/env python3
"""
Update the index.md file with current memory statistics and recent updates.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import re

class IndexUpdater:
    """Update the main index.md file."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
    
    def scan_directory(self, directory: str) -> List[Tuple[str, datetime]]:
        """
        Scan a directory and return list of (filename, modified_time).
        """
        dir_path = self.base_path / directory
        if not dir_path.exists():
            return []
        
        files = []
        for file_path in dir_path.rglob('*.md'):
            if file_path.name != 'index.md':
                rel_path = file_path.relative_to(dir_path)
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                files.append((str(rel_path), mod_time))
        
        return files
    
    def get_statistics(self) -> Dict[str, int]:
        """Gather statistics across all directories."""
        stats = {
            'channels': len(self.scan_directory('channels')),
            'users': len(self.scan_directory('users')),
            'projects': len([f for f in self.scan_directory('projects') 
                           if 'archive' not in f[0].lower()]),
            'tasks': len(self.scan_directory('tasks')),
            'meetings': len(self.scan_directory('meetings')),
            'feedback': len(self.scan_directory('feedback')),
            'decisions': len(self.scan_directory('decisions')),
            'resources': len(self.scan_directory('resources')),
        }
        return stats
    
    def get_recent_updates(self, limit: int = 10) -> List[Tuple[str, str, datetime]]:
        """
        Get the most recent updates across all directories.
        Returns list of (directory, filename, modified_time).
        """
        all_files = []
        
        directories = ['channels', 'users', 'projects', 'tasks', 'meetings', 
                      'feedback', 'decisions', 'announcements', 'resources', 
                      'external/news', 'misc']
        
        for directory in directories:
            files = self.scan_directory(directory)
            for filename, mod_time in files:
                all_files.append((directory, filename, mod_time))
        
        # Sort by modification time, most recent first
        all_files.sort(key=lambda x: x[2], reverse=True)
        
        return all_files[:limit]
    
    def generate_index_content(self) -> str:
        """Generate the complete index.md content."""
        stats = self.get_statistics()
        recent = self.get_recent_updates()
        
        content = f"""# 🧠 Slack Employee Memory Index

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Quick Navigation

### 👥 People & Channels
- **[Channels](channels/)** ({stats['channels']} items) - 슬랙 채널별 정보, 지침, 히스토리
- **[Users](users/)** ({stats['users']} items) - 팀원별 프로필, 커뮤니케이션 스타일, 맞춤 지침

### 📊 Work & Projects
- **[Projects](projects/)** ({stats['projects']} active) - 진행중인 프로젝트 현황 및 히스토리
- **[Tasks](tasks/)** ({stats['tasks']} items) - 수행한 업무 기록
- **[Decisions](decisions/)** ({stats['decisions']} items) - 주요 의사결정 포인트 및 맥락
- **[Meetings](meetings/)** ({stats['meetings']} items) - 회의록 및 액션 아이템

### 💬 Communication & Feedback
- **[Feedback](feedback/)** ({stats['feedback']} items) - 사용자 피드백 및 개선 제안
- **[Announcements](announcements/)** - 중요 공지사항

### 📚 Resources & External
- **[Resources](resources/)** ({stats['resources']} items) - 내부 문서, 가이드, 매뉴얼
- **[External](external/)** - 외부 뉴스, 참고자료

### 🗂️ Other
- **[Misc](misc/)** - 분류되지 않은 정보

---

## 📊 Statistics

- **Total Channels**: {stats['channels']}
- **Total Users**: {stats['users']}
- **Active Projects**: {stats['projects']}
- **Total Tasks**: {stats['tasks']}
- **Total Meetings**: {stats['meetings']}
- **Total Feedback**: {stats['feedback']}

---

## 🔍 Recent Updates

"""
        
        if recent:
            for directory, filename, mod_time in recent:
                # Extract title from filename
                title = Path(filename).stem.replace('_', ' ')
                date_str = mod_time.strftime('%Y-%m-%d %H:%M')
                content += f"- **[{title}]({directory}/{filename})** - {date_str} ({directory})\n"
        else:
            content += "_(No updates yet)_\n"
        
        content += """
---

## 💡 Usage Tips

1. **빠른 검색**: Ctrl+F로 이 인덱스에서 키워드 검색
2. **연결 추적**: 각 파일의 `related_to` 메타데이터로 연결된 정보 확인
3. **히스토리**: 파일의 `updated` 필드로 변경 히스토리 추적
4. **태그**: 파일의 `tags` 메타데이터로 관련 항목 찾기

---

## 📁 Directory Structure

```
├── channels/          슬랙 채널 정보
├── users/             팀원 정보
├── projects/          프로젝트 현황
├── tasks/             업무 기록
│   ├── ongoing/       진행중
│   └── completed/     완료됨
├── meetings/          회의록
├── decisions/         의사결정 히스토리
├── feedback/          피드백
├── announcements/     공지사항
├── resources/         참고자료
├── external/          외부 정보
│   └── news/          뉴스
└── misc/              기타
```
"""
        
        return content
    
    def update_index(self) -> None:
        """Update the index.md file."""
        index_path = self.base_path / 'index.md'
        content = self.generate_index_content()
        index_path.write_text(content, encoding='utf-8')
        print(f"✅ Index updated: {index_path}")

def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: python update_index.py <memory_path>")
        print("Example: python update_index.py /home/claude/employee_memory")
        sys.exit(1)
    
    memory_path = sys.argv[1]
    updater = IndexUpdater(memory_path)
    updater.update_index()
    
    print("\n📊 Index successfully updated!")


if __name__ == "__main__":
    main()
