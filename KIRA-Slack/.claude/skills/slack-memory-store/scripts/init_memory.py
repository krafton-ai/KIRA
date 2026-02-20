#!/usr/bin/env python3
"""
Initialize the employee memory structure.
Creates the base directory structure and index.md file.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def init_memory_structure(base_path: str) -> None:
    """Initialize the memory directory structure."""
    base = Path(base_path)
    
    # Core directories
    directories = [
        "channels",      # 슬랙 채널별 정보
        "users",         # 유저별 정보 및 지침
        "projects",      # 프로젝트 진행사항
        "decisions",     # 의사결정 히스토리
        "tasks",         # 수행한 업무
        "tasks/completed",
        "tasks/ongoing",
        "meetings",      # 회의록
        "feedback",      # 피드백
        "announcements", # 공지사항
        "resources",     # 참고자료/문서
        "external",      # 외부 정보
        "external/news",
        "misc",          # 기타
    ]
    
    for directory in directories:
        dir_path = base / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    # Create index.md
    create_index(base)
    
    # Create .memory_metadata
    create_metadata(base)
    
    print(f"\n🎉 Memory structure initialized at: {base_path}")

def create_index(base_path: Path) -> None:
    """Create the main index.md file."""
    index_content = f"""# 🧠 Slack Employee Memory Index

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Quick Navigation

### 👥 People & Channels
- **[Channels](channels/)** - 슬랙 채널별 정보, 지침, 히스토리
- **[Users](users/)** - 팀원별 프로필, 커뮤니케이션 스타일, 맞춤 지침

### 📊 Work & Projects
- **[Projects](projects/)** - 진행중인 프로젝트 현황 및 히스토리
- **[Tasks](tasks/)** - 수행한 업무 기록
- **[Decisions](decisions/)** - 주요 의사결정 포인트 및 맥락
- **[Meetings](meetings/)** - 회의록 및 액션 아이템

### 💬 Communication & Feedback
- **[Feedback](feedback/)** - 사용자 피드백 및 개선 제안
- **[Announcements](announcements/)** - 중요 공지사항

### 📚 Resources & External
- **[Resources](resources/)** - 내부 문서, 가이드, 매뉴얼
- **[External](external/)** - 외부 뉴스, 참고자료

### 🗂️ Other
- **[Misc](misc/)** - 분류되지 않은 정보

---

## 📊 Statistics

- **Total Channels**: 0
- **Total Users**: 0
- **Active Projects**: 0
- **Total Tasks**: 0

---

## 🔍 Recent Updates

_(No updates yet)_

---

## 💡 Usage Tips

1. **빠른 검색**: 키워드로 관련 파일 찾기
2. **연결 추적**: 파일 간 `related_to` 메타데이터로 연결 확인
3. **히스토리**: 각 파일의 버전 히스토리로 변경사항 추적
"""
    
    index_path = base_path / "index.md"
    index_path.write_text(index_content, encoding='utf-8')
    print(f"✅ Created: index.md")

def create_metadata(base_path: Path) -> None:
    """Create metadata file for tracking."""
    metadata_content = f"""---
created: {datetime.now().isoformat()}
version: 1.0.0
structure_type: slack-memory-store
---
"""
    
    metadata_path = base_path / ".memory_metadata"
    metadata_path.write_text(metadata_content, encoding='utf-8')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init_memory.py <memory_path>")
        print("Example: python init_memory.py /home/claude/employee_memory")
        sys.exit(1)
    
    memory_path = sys.argv[1]
    init_memory_structure(memory_path)
