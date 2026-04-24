import os
import zipfile
import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from app.config import settings


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_count: int = 0
    total_size: int = 0
    index_html_found: bool = False
    extracted_path: Optional[Path] = None
    
    def add_error(self, message: str) -> None:
        self.valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


DANGEROUS_PATTERNS = [
    r"eval\s*\(",
    r"new\s+Function\s*\(",
    r"document\.write\s*\(",
    r"innerHTML\s*=\s*.*\$",
    r"setTimeout\s*\([^,]+,\s*['\"]",
    r"setInterval\s*\([^,]+,\s*['\"]",
    r"<script.*src.*http",
    r"javascript\s*:",
    r"data\s*:.*base64",
]

DANGEROUS_EXTENSIONS = [
    ".php", ".php3", ".php4", ".php5", ".php7", ".phar",
    ".phtml", ".pht", ".phps",
    ".asp", ".aspx", ".ashx", ".asmx", ".aspq",
    ".jsp", ".jspx", ".jhtml", ".jhtm",
    ".cgi", ".pl", ".pm", ".py", ".rb", ".sh",
    ".exe", ".bat", ".cmd", ".com",
    ".dll", ".so", ".dylib",
    ".htaccess", ".htpasswd",
    ".ini", ".conf", ".config",
]


class GameValidator:
    def __init__(self):
        self.settings = settings
    
    def validate_archive(self, archive_path: Path) -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if not archive_path.exists():
            result.add_error(f"Archive file not found: {archive_path}")
            return result
        
        file_size = archive_path.stat().st_size
        if file_size > self.settings.MAX_ARCHIVE_SIZE:
            result.add_error(
                f"Archive too large. Maximum size: {self.settings.MAX_ARCHIVE_SIZE / 1024 / 1024}MB, "
                f"Got: {file_size / 1024 / 1024:.2f}MB"
            )
            return result
        
        ext = archive_path.suffix.lower()
        if ext not in self.settings.ALLOWED_ARCHIVE_EXTENSIONS:
            result.add_error(
                f"Unsupported archive format: {ext}. "
                f"Allowed: {self.settings.ALLOWED_ARCHIVE_EXTENSIONS}"
            )
            return result
        
        return result
    
    def extract_and_validate(
        self, 
        archive_path: Path, 
        extract_to: Path
    ) -> Tuple[ValidationResult, Optional[Path]]:
        result = ValidationResult(valid=True)
        
        archive_validation = self.validate_archive(archive_path)
        if not archive_validation.valid:
            return archive_validation, None
        
        ext = archive_path.suffix.lower()
        
        if ext == ".zip":
            extract_result, game_root = self._extract_zip(archive_path, extract_to)
        elif ext == ".rar":
            extract_result, game_root = self._extract_rar(archive_path, extract_to)
        else:
            result.add_error(f"Unsupported archive format: {ext}")
            return result, None
        
        if not extract_result.valid:
            return extract_result, None
        
        if game_root:
            validation_result = self.validate_game_directory(game_root)
            validation_result.extracted_path = game_root
            return validation_result, game_root
        else:
            result.add_error("No valid game root directory found in archive")
            return result, None
    
    def _extract_zip(
        self, 
        archive_path: Path, 
        extract_to: Path
    ) -> Tuple[ValidationResult, Optional[Path]]:
        result = ValidationResult(valid=True)
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                file_count = len(zf.namelist())
                
                if file_count > self.settings.MAX_FILES_PER_GAME:
                    result.add_error(
                        f"Too many files in archive. Maximum: {self.settings.MAX_FILES_PER_GAME}, "
                        f"Got: {file_count}"
                    )
                    return result, None
                
                dangerous_files = []
                for info in zf.infolist():
                    filename = info.filename
                    
                    if self._is_dangerous_path(filename):
                        dangerous_files.append(filename)
                        continue
                    
                    if self._is_dangerous_extension(filename):
                        dangerous_files.append(filename)
                        continue
                
                if dangerous_files:
                    result.add_error(
                        f"Dangerous files detected: {', '.join(dangerous_files[:5])}"
                    )
                    return result, None
                
                zf.extractall(extract_to)
                
                game_root = self._find_game_root(extract_to)
                
                result.file_count = file_count
                return result, game_root
                
        except zipfile.BadZipFile:
            result.add_error("Invalid ZIP file - corrupted or password protected")
            return result, None
        except Exception as e:
            result.add_error(f"Failed to extract ZIP: {str(e)}")
            return result, None
    
    def _extract_rar(
        self, 
        archive_path: Path, 
        extract_to: Path
    ) -> Tuple[ValidationResult, Optional[Path]]:
        result = ValidationResult(valid=True)
        
        try:
            import rarfile
        except ImportError:
            result.add_warning(
                "RAR support requires 'rarfile' library. "
                "Install with: pip install rarfile"
            )
            result.add_error(
                "RAR archive support is not available. Please use ZIP format instead."
            )
            return result, None
        
        try:
            with rarfile.RarFile(archive_path, 'r') as rf:
                file_count = len(rf.namelist())
                
                if file_count > self.settings.MAX_FILES_PER_GAME:
                    result.add_error(
                        f"Too many files in archive. Maximum: {self.settings.MAX_FILES_PER_GAME}, "
                        f"Got: {file_count}"
                    )
                    return result, None
                
                dangerous_files = []
                for info in rf.infolist():
                    filename = info.filename
                    
                    if self._is_dangerous_path(filename):
                        dangerous_files.append(filename)
                        continue
                    
                    if self._is_dangerous_extension(filename):
                        dangerous_files.append(filename)
                        continue
                
                if dangerous_files:
                    result.add_error(
                        f"Dangerous files detected: {', '.join(dangerous_files[:5])}"
                    )
                    return result, None
                
                rf.extractall(extract_to)
                
                game_root = self._find_game_root(extract_to)
                
                result.file_count = file_count
                return result, game_root
                
        except rarfile.BadRarFile:
            result.add_error("Invalid RAR file - corrupted or password protected")
            return result, None
        except rarfile.RarUnknownError:
            result.add_error("Unknown RAR format - may be newer version or encrypted")
            return result, None
        except Exception as e:
            result.add_error(f"Failed to extract RAR: {str(e)}")
            return result, None
    
    def _find_game_root(self, extract_dir: Path) -> Optional[Path]:
        items = list(extract_dir.iterdir())
        
        if (extract_dir / "index.html").exists():
            return extract_dir
        
        if len(items) == 1 and items[0].is_dir():
            subdir = items[0]
            if (subdir / "index.html").exists():
                return subdir
        
        for item in extract_dir.rglob("index.html"):
            parent = item.parent
            if parent != extract_dir:
                return parent
        
        return None
    
    def _is_dangerous_path(self, filename: str) -> bool:
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            return True
        
        if filename.startswith("~") or filename.startswith("."):
            return True
        
        return False
    
    def _is_dangerous_extension(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in DANGEROUS_EXTENSIONS
    
    def validate_game_directory(self, game_dir: Path) -> ValidationResult:
        result = ValidationResult(valid=True)
        
        index_html = game_dir / "index.html"
        if not index_html.exists():
            result.add_error("index.html not found in game directory")
            return result
        
        result.index_html_found = True
        
        total_size = 0
        file_count = 0
        dangerous_files = []
        
        for item in game_dir.rglob("*"):
            if item.is_file():
                file_count += 1
                file_size = item.stat().st_size
                total_size += file_size
                
                if file_size > self.settings.MAX_FILE_SIZE:
                    result.add_error(
                        f"File too large: {item.name}. "
                        f"Maximum: {self.settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                    )
                
                ext = item.suffix.lower()
                
                if ext in DANGEROUS_EXTENSIONS:
                    dangerous_files.append(item.name)
                
                if ext not in self.settings.ALLOWED_GAME_EXTENSIONS and ext:
                    result.add_warning(
                        f"Uncommon file type: {item.name} (may not work correctly)"
                    )
                
                if ext in [".js", ".html", ".htm"]:
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        for pattern in DANGEROUS_PATTERNS:
                            if re.search(pattern, content, re.IGNORECASE):
                                result.add_warning(
                                    f"Potentially dangerous code pattern found in {item.name}. "
                                    f"Pattern: {pattern}"
                                )
                    except Exception:
                        pass
        
        if dangerous_files:
            result.add_error(
                f"Dangerous file types detected: {', '.join(dangerous_files)}"
            )
        
        if file_count > self.settings.MAX_FILES_PER_GAME:
            result.add_error(
                f"Too many files. Maximum: {self.settings.MAX_FILES_PER_GAME}, Got: {file_count}"
            )
        
        if total_size > self.settings.MAX_GAME_SIZE:
            result.add_error(
                f"Game too large. Maximum: {self.settings.MAX_GAME_SIZE / 1024 / 1024}MB, "
                f"Got: {total_size / 1024 / 1024:.2f}MB"
            )
        
        result.file_count = file_count
        result.total_size = total_size
        
        return result
    
    def validate_index_html(self, index_html: Path) -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if not index_html.exists():
            result.add_error("index.html not found")
            return result
        
        try:
            with open(index_html, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if "<!DOCTYPE" not in content and "<html" not in content.lower():
                result.add_warning("index.html may not be a valid HTML document")
            
            if "<script" in content.lower():
                if "src=" in content.lower():
                    for line in content.lower().split('\n'):
                        if "script" in line and "src=" in line:
                            if "http" in line:
                                result.add_warning(
                                    "External script detected. "
                                    "Scripts should be included locally in your game package."
                                )
            
            if "iframe" in content.lower():
                result.add_warning(
                    "iframe detected. External iframes may not work correctly in the game sandbox."
                )
        
        except Exception as e:
            result.add_warning(f"Could not analyze index.html: {str(e)}")
        
        return result


game_validator = GameValidator()
