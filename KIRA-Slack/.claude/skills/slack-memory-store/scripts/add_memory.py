#!/usr/bin/env python3
"""
Add new information to memory with automatic classification.
Handles various content types: Slack messages, Confluence docs, emails, etc.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class MemoryManager:
    """Manage coworker memory with automatic classification."""

    CONTENT_TYPES = {
        'channel': 'channels',
        'user': 'users',
        'project': 'projects',
        'decision': 'decisions',
        'task': 'tasks',
        'meeting': 'meetings',
        'feedback': 'feedback',
        'announcement': 'announcements',
        'resource': 'resources',
        'news': 'external/news',
        'misc': 'misc'
    }

    # 무효한 식별자 값들
    INVALID_IDENTIFIERS = {
        'unknown', 'not specified', 'n/a', 'none', 'null', '',
        'not_specified', 'unspecified', '미지정', '알수없음',
        'undefined', '없음', '-', 'na'
    }

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _is_valid_identifier(self, value: str) -> bool:
        """식별자가 유효한지 확인"""
        if not value:
            return False
        return value.lower().strip() not in self.INVALID_IDENTIFIERS

    def _parse_frontmatter(self, file_path: Path) -> Dict:
        """YAML frontmatter 파싱"""
        try:
            content = file_path.read_text(encoding='utf-8')
            if not content.startswith('---'):
                return {}

            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}

            # 간단한 YAML 파싱 (yaml 라이브러리 없이)
            metadata = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    metadata[key] = value
            return metadata
        except Exception:
            return {}

    def _find_existing_user_file(self, email: str, user_id: str) -> Optional[Path]:
        """users/ 폴더에서 email 또는 user_id로 기존 파일 검색"""
        users_dir = self.base_path / 'users'
        if not users_dir.exists():
            return None

        for file_path in users_dir.glob('*.md'):
            if file_path.name == 'index.md':
                continue

            metadata = self._parse_frontmatter(file_path)

            # email로 매칭
            file_email = metadata.get('email', '').lower().strip()
            if email and self._is_valid_identifier(email) and self._is_valid_identifier(file_email):
                if file_email == email.lower().strip():
                    return file_path

            # user_id로 매칭
            file_user_id = metadata.get('user_id', '').strip()
            if user_id and self._is_valid_identifier(user_id) and self._is_valid_identifier(file_user_id):
                if file_user_id == user_id.strip():
                    return file_path

        return None

    def _find_existing_channel_file(self, channel_id: str) -> Optional[Path]:
        """channels/ 폴더에서 channel_id로 기존 파일 검색"""
        channels_dir = self.base_path / 'channels'
        if not channels_dir.exists():
            return None

        if not channel_id or not self._is_valid_identifier(channel_id):
            return None

        for file_path in channels_dir.glob('*.md'):
            if file_path.name == 'index.md':
                continue

            metadata = self._parse_frontmatter(file_path)
            file_channel_id = metadata.get('channel_id', '').strip()

            if self._is_valid_identifier(file_channel_id):
                if file_channel_id == channel_id.strip():
                    return file_path

        return None

    def classify_content(self, content: str, metadata: Dict) -> str:
        """
        Automatically classify content based on metadata and content analysis.
        Returns the target directory name.
        """
        # Check explicit type in metadata
        if 'type' in metadata:
            content_type = metadata['type'].lower()
            if content_type in self.CONTENT_TYPES:
                return self.CONTENT_TYPES[content_type]

        # Auto-classify based on keywords and metadata
        content_lower = content.lower()

        # Channel-related
        if any(key in metadata for key in ['channel_id', 'channel_name', 'slack_channel']):
            return 'channels'

        # User-related
        if any(key in metadata for key in ['user_id', 'user_name', 'user_profile']):
            return 'users'

        # Project-related keywords
        project_keywords = ['프로젝트', 'project', '진행상황', 'milestone', '로드맵', 'roadmap']
        if any(keyword in content_lower for keyword in project_keywords):
            return 'projects'

        # Decision-related keywords
        decision_keywords = ['결정', 'decision', '승인', 'approval', '합의', 'agreement']
        if any(keyword in content_lower for keyword in decision_keywords):
            return 'decisions'

        # Task-related keywords
        task_keywords = ['업무', 'task', '완료', 'completed', '수행', 'action item']
        if any(keyword in content_lower for keyword in task_keywords):
            return 'tasks'

        # Meeting-related keywords
        meeting_keywords = ['회의', 'meeting', '미팅', '논의', 'discussion']
        if any(keyword in content_lower for keyword in meeting_keywords):
            return 'meetings'

        # Feedback-related keywords
        feedback_keywords = ['피드백', 'feedback', '개선', 'improvement', '제안', 'suggestion']
        if any(keyword in content_lower for keyword in feedback_keywords):
            return 'feedback'

        # Announcement-related keywords
        announcement_keywords = ['공지', 'announcement', '알림', 'notice']
        if any(keyword in content_lower for keyword in announcement_keywords):
            return 'announcements'

        # News/external keywords
        news_keywords = ['뉴스', 'news', '기사', 'article', '외부', 'external']
        if any(keyword in content_lower for keyword in news_keywords):
            return 'external/news'

        # Default to misc
        return 'misc'

    def generate_filename(self, title: str, metadata: Dict) -> str:
        """Generate a clean filename from title."""
        # Use provided filename if exists
        if 'filename' in metadata:
            return metadata['filename']

        # Clean title for filename
        clean_title = title.strip()
        # Remove special characters
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            clean_title = clean_title.replace(char, '')

        # Replace spaces with underscores for consistency
        clean_title = clean_title.replace(' ', '_')

        # Truncate if too long
        if len(clean_title) > 50:
            clean_title = clean_title[:50]

        # Add date prefix if specified
        if metadata.get('add_date_prefix', False):
            date_prefix = datetime.now().strftime('%Y%m%d')
            clean_title = f"{date_prefix}_{clean_title}"

        return f"{clean_title}.md"

    def format_metadata(self, metadata: Dict) -> str:
        """Format metadata as YAML frontmatter."""
        lines = ["---"]

        # Add created timestamp
        if 'created' not in metadata:
            metadata['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for key, value in metadata.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                # Escape special characters in strings
                if isinstance(value, str) and any(c in value for c in [':', '#', '-']):
                    value = f'"{value}"'
                lines.append(f"{key}: {value}")

        lines.append("---")
        return '\n'.join(lines)

    def add_memory(self, title: str, content: str, metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Add new memory entry.
        Returns (directory, filename) of created file.
        """
        if metadata is None:
            metadata = {}

        # Classify content
        target_dir = self.classify_content(content, metadata)

        # Add classification to metadata
        metadata['category'] = target_dir

        # Check if this is a profile file (channels/ or users/)
        is_profile_file = target_dir in ['channels', 'users']

        # For profile files, try to find existing file by identifier
        existing_file = None
        if is_profile_file:
            if target_dir == 'users':
                email = metadata.get('email', '')
                user_id = metadata.get('user_id', '')
                existing_file = self._find_existing_user_file(email, user_id)
                if existing_file:
                    print(f"🔍 Found existing user file by email/user_id: {existing_file.name}")
            elif target_dir == 'channels':
                channel_id = metadata.get('channel_id', '')
                existing_file = self._find_existing_channel_file(channel_id)
                if existing_file:
                    print(f"🔍 Found existing channel file by channel_id: {existing_file.name}")

        # If existing profile file found, update it
        if existing_file:
            print(f"📝 Updating existing profile: {target_dir}/{existing_file.name}")
            self.update_memory(target_dir, existing_file.name, content, metadata)
            return target_dir, existing_file.name

        # Generate filename for new file
        filename = self.generate_filename(title, metadata)

        # Create full path
        dir_path = self.base_path / target_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path = dir_path / filename

        # Handle existing file with same filename
        if file_path.exists():
            if is_profile_file:
                # Profile files should be updated, not versioned
                print(f"📝 Updating existing profile (same filename): {target_dir}/{filename}")
                self.update_memory(target_dir, filename, content, metadata)
                return target_dir, filename
            else:
                # Topic files can be versioned if same name exists
                base_name = file_path.stem
                counter = 1
                while file_path.exists():
                    filename = f"{base_name}_v{counter}.md"
                    file_path = dir_path / filename
                    counter += 1

        # Format full content
        full_content = f"{self.format_metadata(metadata)}\n\n# {title}\n\n{content}"

        # Write file
        file_path.write_text(full_content, encoding='utf-8')

        print(f"✅ Memory added: {target_dir}/{filename}")
        return target_dir, filename

    def update_memory(self, directory: str, filename: str, new_content: str,
                      new_metadata: Optional[Dict] = None) -> None:
        """Update existing memory entry."""
        file_path = self.base_path / directory / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Memory file not found: {directory}/{filename}")

        # Read existing file
        existing_content = file_path.read_text(encoding='utf-8')

        # Extract existing metadata
        if existing_content.startswith('---'):
            parts = existing_content.split('---', 2)
            if len(parts) >= 3:
                # Parse existing metadata
                existing_metadata = {}
                for line in parts[1].strip().split('\n'):
                    if ':' in line:
                        key, _, value = line.partition(':')
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        existing_metadata[key] = value

                if new_metadata:
                    # Merge metadata (new values override old ones)
                    existing_metadata.update(new_metadata)

                # Add update timestamp
                existing_metadata['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Extract title from new content or existing
                title = ""
                if new_content.startswith('# '):
                    title_line = new_content.split('\n')[0]
                    title = title_line[2:].strip()
                    new_content = '\n'.join(new_content.split('\n')[1:]).strip()

                # Reconstruct file
                if title:
                    full_content = f"{self.format_metadata(existing_metadata)}\n\n# {title}\n\n{new_content}"
                else:
                    full_content = f"{self.format_metadata(existing_metadata)}\n\n{new_content}"

                file_path.write_text(full_content, encoding='utf-8')

                print(f"✅ Memory updated: {directory}/{filename}")
                return

        # If no metadata found, just update content
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✅ Memory updated: {directory}/{filename}")

def main():
    """Main CLI interface."""
    if len(sys.argv) < 4:
        print("Usage: python add_memory.py <memory_path> <title> <content> [metadata_json]")
        print("\nExample:")
        print('  python add_memory.py /memory "마케팅 채널 가이드" "..." \'{"type":"channel"}\'')
        sys.exit(1)

    memory_path = sys.argv[1]
    title = sys.argv[2]
    content = sys.argv[3]

    metadata = {}
    if len(sys.argv) > 4:
        try:
            metadata = json.loads(sys.argv[4])
        except json.JSONDecodeError:
            print("Warning: Invalid JSON metadata, using empty metadata")

    manager = MemoryManager(memory_path)
    directory, filename = manager.add_memory(title, content, metadata)

    print(f"\n📍 Location: {directory}/{filename}")


if __name__ == "__main__":
    main()
