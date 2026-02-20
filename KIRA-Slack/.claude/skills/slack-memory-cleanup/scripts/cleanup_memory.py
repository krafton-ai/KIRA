#!/usr/bin/env python3
"""
Memory Cleanup Script

메모리 폴더를 스캔하여 중복, 오분류, 정리 대상 파일을 탐지합니다.
실제 삭제/이동은 --execute 옵션을 줘야만 수행됩니다.

Usage:
    python cleanup_memory.py <memory_path>                    # 분석만 (dry-run)
    python cleanup_memory.py <memory_path> --execute          # 실제 실행
    python cleanup_memory.py <memory_path> --folder users     # 특정 폴더만
    python cleanup_memory.py <memory_path> --verbose          # 상세 출력
"""

import os
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


class MemoryCleanup:
    """메모리 정리 도구"""

    # memory 스킬과 일치하는 폴더 매핑
    VALID_FOLDERS = {
        'channels', 'users', 'projects', 'tasks', 'decisions',
        'meetings', 'feedback', 'announcements', 'resources',
        'external', 'misc'
    }

    # 프로필 폴더 (1 entity = 1 file 원칙)
    PROFILE_FOLDERS = {'channels', 'users'}

    # 토픽 폴더 (여러 파일 가능)
    TOPIC_FOLDERS = {'projects', 'tasks', 'decisions', 'meetings',
                     'feedback', 'announcements', 'resources', 'misc'}

    # 무효한 식별자 값들
    INVALID_IDENTIFIERS = {
        'unknown', 'not specified', 'n/a', 'none', 'null', '',
        'not_specified', 'unspecified', '미지정', '알수없음',
        'undefined', '없음', '-', 'na'
    }

    # 작업 관련 키워드 (users/에 있으면 안되는 파일)
    TASK_KEYWORDS = {
        '분석', '보고서', '작업', '취합', '성공', '실패', '완료',
        '조회', '처리', '확인', '요청', '결과', 'Report', 'Analysis',
        'Discussion', 'Request', 'Task', 'Issue'
    }

    # channels/에 있으면 안되는 키워드
    NON_CHANNEL_KEYWORDS = {
        '성공', '실패', '완료', '조회', '작업', '처리', '확인',
        '결과', '요청', 'Request', 'Issue', 'Task'
    }

    def __init__(self, base_path: str, verbose: bool = False):
        self.base_path = Path(base_path)
        self.verbose = verbose
        if not self.base_path.exists():
            raise FileNotFoundError(f"Memory path not found: {base_path}")

        self.duplicates: Dict[str, List[Path]] = defaultdict(list)
        self.misclassified: List[Tuple[Path, str, str, str]] = []  # (file, current, suggested, reason)
        self.warnings: List[str] = []

    def log(self, message: str) -> None:
        """verbose 모드에서만 출력"""
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def parse_frontmatter(self, file_path: Path) -> Dict:
        """YAML frontmatter 파싱 (에러 처리 강화)"""
        try:
            content = file_path.read_text(encoding='utf-8')
            if not content.strip():
                self.warnings.append(f"빈 파일: {file_path.name}")
                return {'_empty': True}

            if not content.startswith('---'):
                return {'_no_frontmatter': True}

            parts = content.split('---', 2)
            if len(parts) < 3:
                return {'_invalid_frontmatter': True}

            # 간단한 YAML 파싱 (yaml 라이브러리 없이)
            metadata = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    if value.startswith('[') and value.endswith(']'):
                        # 리스트 처리
                        value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                    metadata[key] = value
            return metadata
        except Exception as e:
            self.warnings.append(f"파일 읽기 실패: {file_path.name} - {str(e)}")
            return {'_error': str(e)}

    def scan_folder(self, folder: str, include_subfolders: bool = True) -> List[Path]:
        """폴더 내 모든 .md 파일 스캔 (하위 폴더 포함 옵션)"""
        folder_path = self.base_path / folder
        if not folder_path.exists():
            return []

        files = []
        if include_subfolders:
            for file_path in folder_path.rglob('*.md'):
                if file_path.name != 'index.md':
                    files.append(file_path)
        else:
            for file_path in folder_path.glob('*.md'):
                if file_path.name != 'index.md':
                    files.append(file_path)
        return files

    def _is_valid_identifier(self, value: str) -> bool:
        """식별자가 유효한지 확인"""
        if not value:
            return False
        return value.lower().strip() not in self.INVALID_IDENTIFIERS

    def _is_valid_channel_id(self, channel_id: str) -> bool:
        """유효한 Slack 채널 ID인지 확인 (C 또는 D로 시작, 충분한 길이)"""
        if not channel_id or not self._is_valid_identifier(channel_id):
            return False
        channel_id = channel_id.strip()
        # Slack 채널 ID: C (채널), D (DM), G (그룹)로 시작, 알파벳+숫자 조합
        return (channel_id[0] in 'CDG' and
                len(channel_id) >= 9 and  # 보통 11자
                channel_id.isalnum())

    def _has_task_keywords(self, filename: str) -> bool:
        """파일명에 작업 관련 키워드가 있는지 확인"""
        return any(kw in filename for kw in self.TASK_KEYWORDS)

    def _has_date_pattern(self, filename: str) -> bool:
        """파일명에 날짜 패턴이 있는지 확인"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2025-12-08
            r'\d{8}',              # 20251208
            r'\d{4}_\d{2}_\d{2}',  # 2025_12_08
        ]
        return any(re.search(pattern, filename) for pattern in date_patterns)

    def _is_profile_file(self, file_path: Path, metadata: Dict) -> bool:
        """순수 프로필 파일인지 판단 (작업 기록이 아닌)"""
        filename = file_path.name

        # 작업 키워드가 있으면 프로필 아님
        if self._has_task_keywords(filename):
            return False

        # 날짜 패턴이 있으면 프로필 아님 (보통 작업 기록)
        if self._has_date_pattern(filename):
            return False

        # '-', '_' 뒤에 긴 설명이 붙어있으면 프로필 아님
        # 예: "전지호 - 이메일 분석.md", "전지호_외부플랫폼초대.md"
        base_name = file_path.stem
        if ' - ' in base_name and len(base_name.split(' - ')[1]) > 5:
            return False

        return True

    # ==================== 중복 탐지 ====================

    def detect_duplicates_users(self) -> Dict[str, List[Tuple[Path, bool]]]:
        """
        users/ 폴더에서 동일인 중복 탐지
        Returns: {identifier: [(file_path, is_profile), ...]}
        """
        files = self.scan_folder('users')
        email_groups: Dict[str, List[Tuple[Path, bool]]] = defaultdict(list)
        user_id_groups: Dict[str, List[Tuple[Path, bool]]] = defaultdict(list)

        for file_path in files:
            metadata = self.parse_frontmatter(file_path)

            email = metadata.get('email', '').lower().strip()
            user_id = metadata.get('user_id', '').strip()
            is_profile = self._is_profile_file(file_path, metadata)

            self.log(f"users/{file_path.name}: email={email}, user_id={user_id}, is_profile={is_profile}")

            if self._is_valid_identifier(email):
                email_groups[email].append((file_path, is_profile))
            if self._is_valid_identifier(user_id):
                user_id_groups[user_id].append((file_path, is_profile))

        # 2개 이상인 그룹 = 중복
        duplicates = {}
        for email, items in email_groups.items():
            if len(items) > 1:
                duplicates[f"email:{email}"] = items

        for user_id, items in user_id_groups.items():
            if len(items) > 1:
                key = f"user_id:{user_id}"
                if key not in duplicates:
                    duplicates[key] = items

        return duplicates

    def detect_duplicates_channels(self) -> Dict[str, List[Path]]:
        """channels/ 폴더에서 동일 채널 중복 탐지"""
        files = self.scan_folder('channels')
        channel_id_groups: Dict[str, List[Path]] = defaultdict(list)

        for file_path in files:
            metadata = self.parse_frontmatter(file_path)
            channel_id = metadata.get('channel_id', '').strip()

            if self._is_valid_channel_id(channel_id):
                channel_id_groups[channel_id].append(file_path)
                self.log(f"channels/{file_path.name}: channel_id={channel_id}")

        return {k: v for k, v in channel_id_groups.items() if len(v) > 1}

    def detect_duplicates_versions(self) -> Dict[str, List[Path]]:
        """버전 파일 (_v1, _v2) 중복 탐지"""
        all_files = []
        for folder in ['projects', 'tasks', 'misc', 'meetings', 'decisions']:
            all_files.extend(self.scan_folder(folder))

        version_pattern = re.compile(r'^(.+)_v(\d+)\.md$')
        base_groups: Dict[str, List[Tuple[Path, int]]] = defaultdict(list)

        for file_path in all_files:
            match = version_pattern.match(file_path.name)
            if match:
                base_name = match.group(1)
                version = int(match.group(2))
                base_groups[base_name].append((file_path, version))

        # 버전이 여러 개인 그룹
        result = {}
        for base_name, items in base_groups.items():
            if len(items) > 1:
                # 버전 순으로 정렬
                items.sort(key=lambda x: x[1])
                result[base_name] = [item[0] for item in items]

        return result

    # ==================== 오분류 탐지 ====================

    def detect_misclassified_channels(self) -> List[Tuple[Path, str, str, str]]:
        """channels/ 폴더의 오분류 파일 탐지"""
        files = self.scan_folder('channels')
        misclassified = []

        for file_path in files:
            filename = file_path.name
            metadata = self.parse_frontmatter(file_path)

            # 1. 메타데이터의 type 필드 확인
            file_type = metadata.get('type', '').lower()
            if file_type and file_type != 'channel':
                suggested = self._get_folder_by_type(file_type)
                misclassified.append((file_path, 'channels', suggested,
                                     f"type이 '{file_type}'"))
                continue

            # 2. 유효한 채널 ID가 없는 파일
            channel_id = metadata.get('channel_id', '').strip()
            if not self._is_valid_channel_id(channel_id):
                # 파일명에 작업 키워드가 있으면 tasks/로
                if any(kw in filename for kw in self.NON_CHANNEL_KEYWORDS):
                    misclassified.append((file_path, 'channels', 'tasks',
                                         "작업 키워드 포함 + 유효한 channel_id 없음"))
                else:
                    misclassified.append((file_path, 'channels', 'misc',
                                         "유효한 channel_id 없음"))
                continue

            # 3. 채널 ID가 있지만 파일명이 채널 ID로 시작하지 않는 경우
            if not filename.startswith(channel_id[0]):
                if any(kw in filename for kw in self.NON_CHANNEL_KEYWORDS):
                    misclassified.append((file_path, 'channels', 'tasks',
                                         f"작업 키워드 포함 (channel_id: {channel_id})"))

        return misclassified

    def detect_misclassified_users(self) -> List[Tuple[Path, str, str, str]]:
        """users/ 폴더의 오분류 파일 탐지 (작업 기록이 프로필에 섞인 경우)"""
        files = self.scan_folder('users')
        misclassified = []

        for file_path in files:
            filename = file_path.name
            metadata = self.parse_frontmatter(file_path)

            # 1. 메타데이터의 type 필드 확인
            file_type = metadata.get('type', '').lower()
            if file_type and file_type not in ['user', 'profile', '']:
                suggested = self._get_folder_by_type(file_type)
                misclassified.append((file_path, 'users', suggested,
                                     f"type이 '{file_type}'"))
                continue

            # 2. 프로필 파일이 아닌 경우 (작업 기록)
            if not self._is_profile_file(file_path, metadata):
                # 날짜 패턴이 있으면 tasks/
                if self._has_date_pattern(filename):
                    misclassified.append((file_path, 'users', 'tasks',
                                         "파일명에 날짜 패턴"))
                # 작업 키워드가 있으면 tasks/
                elif self._has_task_keywords(filename):
                    misclassified.append((file_path, 'users', 'tasks',
                                         "파일명에 작업 키워드"))
                # Discussion 등은 misc/
                elif 'Discussion' in filename or '대화' in filename:
                    misclassified.append((file_path, 'users', 'misc',
                                         "대화/토론 기록"))

        return misclassified

    def detect_misclassified_by_type(self) -> List[Tuple[Path, str, str, str]]:
        """모든 폴더에서 type 메타데이터와 폴더가 불일치하는 파일 탐지"""
        misclassified = []

        type_to_folder = {
            'channel': 'channels',
            'user': 'users',
            'project': 'projects',
            'task': 'tasks',
            'decision': 'decisions',
            'meeting': 'meetings',
            'feedback': 'feedback',
            'announcement': 'announcements',
            'resource': 'resources',
            'news': 'external/news',
        }

        for folder in self.VALID_FOLDERS:
            files = self.scan_folder(folder)
            for file_path in files:
                metadata = self.parse_frontmatter(file_path)
                file_type = metadata.get('type', '').lower()

                if file_type and file_type in type_to_folder:
                    expected_folder = type_to_folder[file_type]
                    # 현재 폴더와 기대 폴더가 다르면 오분류
                    current_folder = str(file_path.parent.relative_to(self.base_path)).split('/')[0]
                    if current_folder != expected_folder.split('/')[0]:
                        # 이미 다른 규칙에서 탐지했을 수 있으므로 중복 체크
                        if not any(m[0] == file_path for m in misclassified):
                            misclassified.append((file_path, current_folder, expected_folder,
                                                 f"type='{file_type}'이지만 {current_folder}/에 있음"))

        return misclassified

    def _get_folder_by_type(self, file_type: str) -> str:
        """type 값에 따른 권장 폴더 반환"""
        # 기본 매핑
        type_mapping = {
            'channel': 'channels',
            'user': 'users',
            'profile': 'users',
            'project': 'projects',
            'task': 'tasks',
            'decision': 'decisions',
            'meeting': 'meetings',
            'feedback': 'feedback',
            'announcement': 'announcements',
            'resource': 'resources',
            'news': 'external/news',
        }

        # 정확히 매칭되면 반환
        if file_type in type_mapping:
            return type_mapping[file_type]

        # 변형된 type 처리 (task_completed, task_result 등)
        if file_type.startswith('task'):
            return 'tasks'
        if file_type.startswith('project'):
            return 'projects'
        if file_type.startswith('meeting'):
            return 'meetings'
        if file_type.startswith('decision'):
            return 'decisions'

        return 'misc'

    # ==================== 리포트 생성 ====================

    def analyze(self, folder: Optional[str] = None) -> Dict:
        """전체 분석 수행"""
        result = {
            'duplicates': {
                'users': {},
                'channels': {},
                'versions': {}
            },
            'misclassified': [],
            'warnings': [],
            'summary': {}
        }

        if folder is None or folder == 'users':
            result['duplicates']['users'] = self.detect_duplicates_users()
            result['misclassified'].extend(self.detect_misclassified_users())

        if folder is None or folder == 'channels':
            result['duplicates']['channels'] = self.detect_duplicates_channels()
            result['misclassified'].extend(self.detect_misclassified_channels())

        if folder is None:
            result['duplicates']['versions'] = self.detect_duplicates_versions()
            # type 필드 기반 오분류 탐지
            type_misclassified = self.detect_misclassified_by_type()
            for item in type_misclassified:
                if not any(m[0] == item[0] for m in result['misclassified']):
                    result['misclassified'].append(item)

        # 경고 수집
        result['warnings'] = self.warnings

        # 요약 계산
        total_duplicates = (
            len(result['duplicates']['users']) +
            len(result['duplicates']['channels']) +
            len(result['duplicates']['versions'])
        )
        result['summary'] = {
            'total_duplicate_groups': total_duplicates,
            'total_misclassified': len(result['misclassified']),
            'total_warnings': len(self.warnings)
        }

        return result

    def print_report(self, result: Dict) -> None:
        """분석 결과 출력"""
        print("\n" + "=" * 60)
        print("📊 메모리 정리 분석 결과")
        print("=" * 60)

        # 중복 파일
        print("\n## 🔴 중복 파일")

        if result['duplicates']['users']:
            print("\n### users/ 폴더 (동일인 중복)")
            for key, items in result['duplicates']['users'].items():
                print(f"\n  {key}:")
                for item in items:
                    if isinstance(item, tuple):
                        path, is_profile = item
                        status = "✅ 프로필" if is_profile else "📝 작업기록"
                        print(f"    - {path.name} ({status})")
                    else:
                        print(f"    - {item.name}")

        if result['duplicates']['channels']:
            print("\n### channels/ 폴더 (동일 채널 중복)")
            for key, paths in result['duplicates']['channels'].items():
                print(f"\n  channel_id: {key}:")
                for p in paths:
                    print(f"    - {p.name}")

        if result['duplicates']['versions']:
            print("\n### 버전 파일 중복")
            for key, paths in result['duplicates']['versions'].items():
                print(f"\n  {key}:")
                for i, p in enumerate(paths):
                    status = "← 최신" if i == len(paths) - 1 else "← 삭제 가능"
                    print(f"    - {p.name} {status}")

        if not any(result['duplicates'].values()):
            print("  (중복 없음)")

        # 오분류 파일
        print("\n## 🟡 오분류 파일")
        if result['misclassified']:
            for item in result['misclassified']:
                if len(item) == 4:
                    file_path, current, suggested, reason = item
                    print(f"  {file_path.name}")
                    print(f"    현재: {current}/ → 권장: {suggested}/")
                    print(f"    이유: {reason}")
                else:
                    file_path, current, suggested = item
                    print(f"  {file_path.name}")
                    print(f"    현재: {current}/ → 권장: {suggested}/")
        else:
            print("  (오분류 없음)")

        # 경고
        if result['warnings']:
            print("\n## ⚠️ 경고")
            for warning in result['warnings']:
                print(f"  - {warning}")

        # 요약
        print("\n## 📈 요약")
        print(f"  - 중복 그룹: {result['summary']['total_duplicate_groups']}개")
        print(f"  - 오분류 파일: {result['summary']['total_misclassified']}개")
        if result['summary']['total_warnings'] > 0:
            print(f"  - 경고: {result['summary']['total_warnings']}개")
        print("\n" + "=" * 60)

    # ==================== 실행 ====================

    def execute_cleanup(self, result: Dict, dry_run: bool = True) -> None:
        """정리 실행 (dry_run=False일 때만 실제 수행)"""
        if dry_run:
            print("\n⚠️  DRY RUN 모드 - 실제 변경 없음")
            print("   실제 실행하려면 --execute 옵션 사용")
            return

        print("\n🔧 정리 실행 중...")
        moved_count = 0

        # 오분류 파일 이동
        for item in result['misclassified']:
            file_path = item[0]
            suggested = item[2]

            dest_folder = self.base_path / suggested
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / file_path.name

            # 중복 파일명 처리
            if dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_folder / f"{stem}_{counter}{suffix}"
                    counter += 1

            print(f"  이동: {file_path.name}")
            print(f"    {item[1]}/ → {suggested}/")
            shutil.move(str(file_path), str(dest_path))
            moved_count += 1

        print(f"\n✅ 정리 완료! ({moved_count}개 파일 이동)")
        print("   index.md 업데이트를 권장합니다:")
        print(f"   python scripts/update_index.py {self.base_path}")


def main():
    """CLI 인터페이스"""
    if len(sys.argv) < 2:
        print("Usage: python cleanup_memory.py <memory_path> [options]")
        print("")
        print("Options:")
        print("  --execute       실제 정리 실행 (기본은 분석만)")
        print("  --folder NAME   특정 폴더만 분석 (users, channels)")
        print("  --verbose       상세 디버그 출력")
        print("")
        print("Examples:")
        print("  python cleanup_memory.py ~/Documents/KIRA/memories")
        print("  python cleanup_memory.py ~/Documents/KIRA/memories --execute")
        print("  python cleanup_memory.py ~/Documents/KIRA/memories --folder users")
        print("  python cleanup_memory.py ~/Documents/KIRA/memories --verbose")
        sys.exit(1)

    memory_path = sys.argv[1]
    execute = '--execute' in sys.argv
    verbose = '--verbose' in sys.argv

    folder = None
    if '--folder' in sys.argv:
        idx = sys.argv.index('--folder')
        if idx + 1 < len(sys.argv):
            folder = sys.argv[idx + 1]

    try:
        cleanup = MemoryCleanup(memory_path, verbose=verbose)
        result = cleanup.analyze(folder)
        cleanup.print_report(result)
        cleanup.execute_cleanup(result, dry_run=not execute)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)



if __name__ == "__main__":
    main()
