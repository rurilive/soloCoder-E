import os
import re
from typing import List, Tuple
from ebooklib import epub
from bs4 import BeautifulSoup


class BookParser:
    @staticmethod
    def parse_epub(file_path: str) -> Tuple[str, str, List[Tuple[str, str]]]:
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
                for h_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if h_tag.get_text(strip=True):
                        chapter_title = h_tag.get_text(strip=True)
                        break
                
                for script in soup(['script', 'style']):
                    script.decompose()
                
                text_content = soup.get_text(separator='\n', strip=True)
                
                if text_content:
                    chapters.append((chapter_title, text_content))
                    order += 1
        
        if not chapters:
            chapters.append(("Untitled", "No content found"))
        
        return title, author, chapters

    @staticmethod
    def parse_txt(file_path: str) -> Tuple[str, str, List[Tuple[str, str]]]:
        filename = os.path.basename(file_path)
        title, _ = os.path.splitext(filename)
        author = "Unknown Author"
        
        chapters = []
        order = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
        
        lines = content.split('\n')
        
        chapter_patterns = [
            r'^第[一二三四五六七八九十百千零\d]+[章节回]',
            r'^Chapter\s+\d+',
            r'^\d+\s+[A-Za-z]',
            r'^第\s*\d+\s*[章节回]',
        ]
        
        current_chapter_title = "Introduction"
        current_chapter_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_chapter_title = False
            for pattern in chapter_patterns:
                if re.match(pattern, line):
                    is_chapter_title = True
                    break
            
            if is_chapter_title:
                if current_chapter_content:
                    chapters.append((current_chapter_title, '\n'.join(current_chapter_content)))
                    order += 1
                
                current_chapter_title = line
                current_chapter_content = []
            else:
                current_chapter_content.append(line)
        
        if current_chapter_content:
            chapters.append((current_chapter_title, '\n'.join(current_chapter_content)))
        
        if not chapters:
            chapters.append(("Untitled", content))
        
        return title, author, chapters

    @staticmethod
    def parse(file_path: str) -> Tuple[str, str, List[Tuple[str, str]]]:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.epub':
            return BookParser.parse_epub(file_path)
        elif ext == '.txt':
            return BookParser.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
