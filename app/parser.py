import os
import re
from typing import List, Tuple, Optional, Dict, Any
from ebooklib import epub
from bs4 import BeautifulSoup


class ChapterPattern:
    def __init__(self, pattern: str, level: int = 1, name: str = ""):
        self.pattern = pattern
        self.level = level
        self.name = name or pattern


class ChapterRecognizer:
    CHAPTER_PATTERNS = [
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+卷\s*', level=0, name="卷"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*卷\s*', level=0, name="卷"),
        ChapterPattern(r'^卷[一二三四五六七八九十百千零\d]+\s*', level=0, name="卷"),
        ChapterPattern(r'^[上下中前後后]部\s*', level=0, name="部"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+部\s*', level=0, name="部"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*部\s*', level=0, name="部"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+篇\s*', level=0, name="篇"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*篇\s*', level=0, name="篇"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+[章节回]', level=1, name="章节"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*[章节回]', level=1, name="章节"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+话', level=1, name="话"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*话', level=1, name="话"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+集', level=1, name="集"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*集', level=1, name="集"),
        ChapterPattern(r'^第[一二三四五六七八九十百千零\d]+幕', level=1, name="幕"),
        ChapterPattern(r'^第\s*[一二三四五六七八九十百千零\d]+\s*幕', level=1, name="幕"),
        ChapterPattern(r'^Chapter\s+\d+', level=1, name="Chapter"),
        ChapterPattern(r'^chapter\s+\d+', level=1, name="chapter"),
        ChapterPattern(r'^CH\.?\s*\d+', level=1, name="CH"),
        ChapterPattern(r'^Part\s+\d+', level=0, name="Part"),
        ChapterPattern(r'^part\s+\d+', level=0, name="part"),
        ChapterPattern(r'^Book\s+\d+', level=0, name="Book"),
        ChapterPattern(r'^book\s+\d+', level=0, name="book"),
        ChapterPattern(r'^Section\s+\d+', level=1, name="Section"),
        ChapterPattern(r'^section\s+\d+', level=1, name="section"),
        ChapterPattern(r'^Act\s+\d+', level=0, name="Act"),
        ChapterPattern(r'^Scene\s+\d+', level=1, name="Scene"),
        ChapterPattern(r'^\d+\.\s+', level=1, name="数字序号"),
        ChapterPattern(r'^\d+\.\d+\s+', level=2, name="二级数字序号"),
        ChapterPattern(r'^\d+、\s*', level=1, name="数字顿号"),
        ChapterPattern(r'^[一二三四五六七八九十]+、\s*', level=1, name="中文数字顿号"),
        ChapterPattern(r'^[（(]\d+[）)]\s*', level=1, name="括号数字"),
        ChapterPattern(r'^[（(][一二三四五六七八九十]+[）)]\s*', level=1, name="括号中文数字"),
        ChapterPattern(r'^\d+\s+[^\s]', level=1, name="数字加标题"),
    ]

    @classmethod
    def is_chapter_title(cls, line: str) -> Tuple[bool, int, str]:
        stripped_line = line.strip()
        if not stripped_line:
            return False, 0, ""

        for pattern in cls.CHAPTER_PATTERNS:
            if re.match(pattern.pattern, stripped_line, re.UNICODE):
                return True, pattern.level, pattern.name

        return False, 0, ""

    @classmethod
    def extract_chapter_number(cls, line: str) -> Optional[str]:
        stripped_line = line.strip()

        patterns = [
            (r'^第([一二三四五六七八九十百千零\d]+)[章节回卷篇部话集幕]', 1),
            (r'^第\s*([一二三四五六七八九十百千零\d]+)\s*[章节回卷篇部话集幕]', 1),
            (r'^卷([一二三四五六七八九十百千零\d]+)', 1),
            (r'^Chapter\s+(\d+)', 1),
            (r'^Part\s+(\d+)', 1),
            (r'^Book\s+(\d+)', 1),
            (r'^Section\s+(\d+)', 1),
            (r'^Act\s+(\d+)', 1),
            (r'^Scene\s+(\d+)', 1),
            (r'^(\d+)\.\s+', 1),
            (r'^(\d+\.\d+)\s+', 1),
            (r'^(\d+)、\s*', 1),
        ]

        for pattern, group_num in patterns:
            match = re.match(pattern, stripped_line, re.UNICODE)
            if match:
                return match.group(group_num)

        return None


class BookParser:
    @staticmethod
    def parse_epub(file_path: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        book = epub.read_epub(file_path)

        title = "Unknown Title"
        author = "Unknown Author"

        for metadata in book.get_metadata('DC', 'title'):
            title = metadata[0]
            break

        for metadata in book.get_metadata('DC', 'creator'):
            author = metadata[0]
            break

        chapters = []
        order = 0

        for item in book.get_items():
            if item.get_type() == 9:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'html.parser')

                chapter_title = f"Chapter {order + 1}"
                chapter_level = 1

                for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    text = h_tag.get_text(strip=True)
                    if text:
                        is_chapter, level, name = ChapterRecognizer.is_chapter_title(text)
                        if is_chapter or len(text) < 50:
                            chapter_title = text
                            tag_level = int(h_tag.name[1]) - 1
                            chapter_level = min(level if is_chapter else tag_level, 2)
                            break

                for script in soup(['script', 'style']):
                    script.decompose()

                text_content = soup.get_text(separator='\n', strip=True)

                if text_content:
                    chapters.append({
                        'title': chapter_title,
                        'content': text_content,
                        'level': chapter_level
                    })
                    order += 1

        if not chapters:
            chapters.append({
                'title': "Untitled",
                'content': "No content found",
                'level': 1
            })

        return title, author, chapters

    @staticmethod
    def parse_txt(file_path: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        filename = os.path.basename(file_path)
        title, _ = os.path.splitext(filename)
        author = "Unknown Author"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()

        lines = content.split('\n')

        chapters = []
        current_chapter_title = "Introduction"
        current_chapter_content = []
        current_chapter_level = 1
        order = 0

        consecutive_empty_lines = 0
        min_content_lines = 3

        for line in lines:
            stripped_line = line.strip()

            if not stripped_line:
                consecutive_empty_lines += 1
                if current_chapter_content:
                    current_chapter_content.append("")
                continue

            consecutive_empty_lines = 0

            is_chapter, level, pattern_name = ChapterRecognizer.is_chapter_title(stripped_line)

            if is_chapter:
                if current_chapter_content and any(c.strip() for c in current_chapter_content):
                    content_text = '\n'.join(current_chapter_content).strip()
                    if content_text:
                        chapters.append({
                            'title': current_chapter_title,
                            'content': content_text,
                            'level': current_chapter_level
                        })
                        order += 1

                current_chapter_title = stripped_line
                current_chapter_content = []
                current_chapter_level = level
            else:
                if len(stripped_line) < 100 and not stripped_line.endswith(('。', '！', '？', '，', '；', '：')):
                    is_chapter2, _, _ = ChapterRecognizer.is_chapter_title(stripped_line)
                    if not is_chapter2 and re.match(r'^[^\d\s]', stripped_line):
                        if current_chapter_content and any(c.strip() for c in current_chapter_content):
                            content_lines = [c for c in current_chapter_content if c.strip()]
                            if len(content_lines) >= min_content_lines:
                                content_text = '\n'.join(current_chapter_content).strip()
                                if content_text:
                                    chapters.append({
                                        'title': current_chapter_title,
                                        'content': content_text,
                                        'level': current_chapter_level
                                    })
                                    order += 1

                        current_chapter_title = stripped_line
                        current_chapter_content = []
                        current_chapter_level = 1
                        continue

                current_chapter_content.append(stripped_line)

        if current_chapter_content and any(c.strip() for c in current_chapter_content):
            content_text = '\n'.join(current_chapter_content).strip()
            if content_text:
                chapters.append({
                    'title': current_chapter_title,
                    'content': content_text,
                    'level': current_chapter_level
                })

        if not chapters:
            chapters.append({
                'title': "Untitled",
                'content': content,
                'level': 1
            })

        return title, author, chapters

    @staticmethod
    def parse(file_path: str) -> Tuple[str, str, List[Dict[str, Any]]]:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.epub':
            return BookParser.parse_epub(file_path)
        elif ext == '.txt':
            return BookParser.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
