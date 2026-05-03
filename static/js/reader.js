document.addEventListener('DOMContentLoaded', function() {
    const bookId = window.bookId;
    
    let currentChapterIndex = 0;
    let chapters = [];
    let currentChapterId = null;
    let fontSize = 16;
    let lineHeight = 1.8;
    let currentTheme = 'light';
    
    const state = {
        chapterIndex: 0,
        scrollPosition: 0
    };
    
    loadSettings();
    loadBook();
    initEventListeners();
    
    function loadSettings() {
        const savedFontSize = localStorage.getItem('ereader_fontSize');
        const savedLineHeight = localStorage.getItem('ereader_lineHeight');
        const savedTheme = localStorage.getItem('ereader_theme');
        
        if (savedFontSize) {
            fontSize = parseInt(savedFontSize);
            updateFontSize();
        }
        
        if (savedLineHeight) {
            lineHeight = parseFloat(savedLineHeight);
            updateLineHeight();
        }
        
        if (savedTheme) {
            currentTheme = savedTheme;
            applyTheme();
        }
    }
    
    function loadBook() {
        fetch(`/books/${bookId}`)
            .then(response => response.json())
            .then(book => {
                chapters = book.chapters;
                renderTOC();
                
                if (chapters.length > 0) {
                    loadChapter(0);
                }
            })
            .catch(error => {
                console.error('Error loading book:', error);
                showMessage('加载书籍失败', 'error');
            });
    }
    
    function loadChapter(index, scrollToTop = true) {
        if (index < 0 || index >= chapters.length) return;
        
        const chapter = chapters[index];
        currentChapterIndex = index;
        currentChapterId = chapter.id;
        
        fetch(`/chapters/${chapter.id}`)
            .then(response => response.json())
            .then(chapterData => {
                const pageContent = document.getElementById('pageContent');
                pageContent.innerHTML = formatContent(chapterData.content);
                
                document.getElementById('currentChapterTitle').textContent = chapter.title;
                
                updateChapterButtons();
                highlightCurrentTOC();
                
                if (scrollToTop) {
                    pageContent.scrollTop = 0;
                    updateProgress();
                }
                
                state.chapterIndex = index;
            })
            .catch(error => {
                console.error('Error loading chapter:', error);
                showMessage('加载章节失败', 'error');
            });
    }
    
    function formatContent(content) {
        const paragraphs = content.split('\n\n');
        return paragraphs.map(p => {
            const trimmed = p.trim();
            if (trimmed) {
                return `<p>${escapeHtml(trimmed)}</p>`;
            }
            return '';
        }).join('');
    }
    
    function updateChapterButtons() {
        const prevBtn = document.getElementById('prevChapterBtn');
        const nextBtn = document.getElementById('nextChapterBtn');
        
        prevBtn.disabled = currentChapterIndex === 0;
        nextBtn.disabled = currentChapterIndex === chapters.length - 1;
        
        prevBtn.style.opacity = currentChapterIndex === 0 ? '0.5' : '1';
        nextBtn.style.opacity = currentChapterIndex === chapters.length - 1 ? '0.5' : '1';
    }
    
    function renderTOC() {
        const tocContent = document.getElementById('tocContent');
        tocContent.innerHTML = '';
        
        chapters.forEach((chapter, index) => {
            const item = document.createElement('div');
            item.className = 'toc-item';
            item.dataset.index = index;
            item.innerHTML = `
                <div class="toc-title">${escapeHtml(chapter.title)}</div>
                <div class="toc-order">第 ${index + 1} 章</div>
            `;
            
            item.addEventListener('click', () => {
                loadChapter(index);
                closeAllSidebars();
            });
            
            tocContent.appendChild(item);
        });
    }
    
    function highlightCurrentTOC() {
        const items = document.querySelectorAll('.toc-item');
        items.forEach((item, index) => {
            item.classList.toggle('active', index === currentChapterIndex);
        });
    }
    
    function loadBookmarks() {
        fetch(`/bookmarks/${bookId}`)
            .then(response => response.json())
            .then(bookmarks => {
                renderBookmarks(bookmarks);
            })
            .catch(error => {
                console.error('Error loading bookmarks:', error);
            });
    }
    
    function renderBookmarks(bookmarks) {
        const bookmarksContent = document.getElementById('bookmarksContent');
        
        if (bookmarks.length === 0) {
            bookmarksContent.innerHTML = '<p style="padding: 20px; text-align: center; color: var(--text-secondary);">暂无书签</p>';
            return;
        }
        
        bookmarksContent.innerHTML = '';
        
        bookmarks.forEach(bookmark => {
            const item = document.createElement('div');
            item.className = 'bookmark-item';
            
            const date = new Date(bookmark.created_at).toLocaleString('zh-CN');
            
            item.innerHTML = `
                <div class="bookmark-info" data-chapter-id="${bookmark.chapter_id}">
                    <div class="bookmark-chapter">${escapeHtml(bookmark.chapter_title)}</div>
                    ${bookmark.note ? `<div class="bookmark-note">${escapeHtml(bookmark.note)}</div>` : ''}
                    <div class="bookmark-time">${date}</div>
                </div>
                <div class="bookmark-actions">
                    <button class="btn btn-icon delete-bookmark" data-id="${bookmark.id}" title="删除书签">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            `;
            
            const info = item.querySelector('.bookmark-info');
            info.addEventListener('click', () => {
                const chapterIndex = chapters.findIndex(c => c.id === bookmark.chapter_id);
                if (chapterIndex !== -1) {
                    loadChapter(chapterIndex);
                    closeAllSidebars();
                }
            });
            
            const deleteBtn = item.querySelector('.delete-bookmark');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('确定要删除这个书签吗？')) {
                    deleteBookmark(bookmark.id);
                }
            });
            
            bookmarksContent.appendChild(item);
        });
    }
    
    function deleteBookmark(bookmarkId) {
        fetch(`/bookmarks/${bookmarkId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                showMessage('书签删除成功', 'success');
                loadBookmarks();
            } else {
                showMessage('删除失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting bookmark:', error);
            showMessage('删除失败', 'error');
        });
    }
    
    function updateProgress() {
        const pageContent = document.getElementById('pageContent');
        const progressSlider = document.getElementById('progressSlider');
        const progressText = document.getElementById('progressText');
        
        const scrollTop = pageContent.scrollTop;
        const scrollHeight = pageContent.scrollHeight - pageContent.clientHeight;
        
        if (scrollHeight > 0) {
            const progress = (scrollTop / scrollHeight) * 100;
            progressSlider.value = progress;
            progressText.textContent = `${Math.round(progress)}%`;
        }
    }
    
    function updateFontSize() {
        const pageContent = document.getElementById('pageContent');
        pageContent.style.fontSize = fontSize + 'px';
        document.getElementById('fontSizeValue').textContent = fontSize + 'px';
        localStorage.setItem('ereader_fontSize', fontSize);
    }
    
    function updateLineHeight() {
        const pageContent = document.getElementById('pageContent');
        pageContent.style.lineHeight = lineHeight;
        document.getElementById('lineHeightValue').textContent = lineHeight.toFixed(1);
        localStorage.setItem('ereader_lineHeight', lineHeight);
    }
    
    function applyTheme() {
        document.body.className = `theme-${currentTheme}`;
        
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === currentTheme);
        });
        
        localStorage.setItem('ereader_theme', currentTheme);
    }
    
    function openSidebar(sidebarId) {
        closeAllSidebars();
        
        const sidebar = document.getElementById(sidebarId);
        const overlay = document.getElementById('overlay');
        
        sidebar.classList.add('open');
        overlay.classList.add('active');
        
        if (sidebarId === 'bookmarksSidebar') {
            loadBookmarks();
        }
    }
    
    function closeAllSidebars() {
        document.querySelectorAll('.sidebar, .settings-panel').forEach(el => {
            el.classList.remove('open');
        });
        document.getElementById('overlay').classList.remove('active');
    }
    
    function toggleHeaderControls(show) {
        const header = document.getElementById('readerHeader');
        const chapterNav = document.getElementById('chapterNav');
        const readingProgress = document.getElementById('readingProgress');
        
        if (show) {
            header.classList.remove('hidden');
            chapterNav.classList.remove('hidden');
            readingProgress.classList.remove('hidden');
        } else {
            header.classList.add('hidden');
            chapterNav.classList.add('hidden');
            readingProgress.classList.add('hidden');
        }
    }
    
    function showBookmarkModal() {
        const modal = document.getElementById('bookmarkModal');
        const overlay = document.getElementById('overlay');
        
        document.getElementById('bookmarkNote').value = '';
        
        modal.classList.add('active');
        overlay.classList.add('active');
    }
    
    function closeBookmarkModal() {
        const modal = document.getElementById('bookmarkModal');
        const overlay = document.getElementById('overlay');
        
        modal.classList.remove('active');
        overlay.classList.remove('active');
    }
    
    function saveBookmark() {
        const note = document.getElementById('bookmarkNote').value.trim();
        
        const pageContent = document.getElementById('pageContent');
        const position = pageContent.scrollTop;
        
        fetch('/bookmarks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                book_id: bookId,
                chapter_id: currentChapterId,
                position: position,
                note: note
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                showMessage('书签保存成功', 'success');
                closeBookmarkModal();
            } else {
                showMessage('保存失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving bookmark:', error);
            showMessage('保存失败', 'error');
        });
    }
    
    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = message;
        
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease;
        `;
        
        if (type === 'success') {
            messageDiv.style.backgroundColor = '#d4edda';
            messageDiv.style.color = '#155724';
            messageDiv.style.border = '1px solid #c3e6cb';
        } else if (type === 'error') {
            messageDiv.style.backgroundColor = '#f8d7da';
            messageDiv.style.color = '#721c24';
            messageDiv.style.border = '1px solid #f5c6cb';
        } else {
            messageDiv.style.backgroundColor = '#cce5ff';
            messageDiv.style.color = '#004085';
            messageDiv.style.border = '1px solid #b8daff';
        }
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                messageDiv.remove();
            }, 300);
        }, 3000);
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function initEventListeners() {
        document.getElementById('backBtn').addEventListener('click', () => {
            window.location.href = '/';
        });
        
        document.getElementById('prevChapterBtn').addEventListener('click', () => {
            if (currentChapterIndex > 0) {
                loadChapter(currentChapterIndex - 1);
            }
        });
        
        document.getElementById('nextChapterBtn').addEventListener('click', () => {
            if (currentChapterIndex < chapters.length - 1) {
                loadChapter(currentChapterIndex + 1);
            }
        });
        
        document.getElementById('tocBtn').addEventListener('click', () => {
            openSidebar('tocSidebar');
        });
        
        document.getElementById('closeTocBtn').addEventListener('click', closeAllSidebars);
        
        document.getElementById('bookmarksBtn').addEventListener('click', () => {
            openSidebar('bookmarksSidebar');
        });
        
        document.getElementById('closeBookmarksBtn').addEventListener('click', closeAllSidebars);
        
        document.getElementById('settingsBtn').addEventListener('click', () => {
            closeAllSidebars();
            const settingsPanel = document.getElementById('settingsPanel');
            const overlay = document.getElementById('overlay');
            settingsPanel.classList.add('open');
            overlay.classList.add('active');
        });
        
        document.getElementById('closeSettingsBtn').addEventListener('click', closeAllSidebars);
        
        document.getElementById('overlay').addEventListener('click', () => {
            closeAllSidebars();
            closeBookmarkModal();
        });
        
        document.getElementById('decreaseFontBtn').addEventListener('click', () => {
            if (fontSize > 12) {
                fontSize -= 2;
                updateFontSize();
            }
        });
        
        document.getElementById('increaseFontBtn').addEventListener('click', () => {
            if (fontSize < 28) {
                fontSize += 2;
                updateFontSize();
            }
        });
        
        document.getElementById('decreaseLineHeightBtn').addEventListener('click', () => {
            if (lineHeight > 1.2) {
                lineHeight -= 0.2;
                updateLineHeight();
            }
        });
        
        document.getElementById('increaseLineHeightBtn').addEventListener('click', () => {
            if (lineHeight < 3.0) {
                lineHeight += 0.2;
                updateLineHeight();
            }
        });
        
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentTheme = btn.dataset.theme;
                applyTheme();
            });
        });
        
        const pageContent = document.getElementById('pageContent');
        pageContent.addEventListener('scroll', updateProgress);
        
        const progressSlider = document.getElementById('progressSlider');
        progressSlider.addEventListener('input', (e) => {
            const value = e.target.value;
            const scrollHeight = pageContent.scrollHeight - pageContent.clientHeight;
            pageContent.scrollTop = (value / 100) * scrollHeight;
        });
        
        let controlsVisible = true;
        pageContent.addEventListener('click', (e) => {
            if (e.target === pageContent || e.target.tagName === 'P') {
                controlsVisible = !controlsVisible;
                toggleHeaderControls(controlsVisible);
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
                if (currentChapterIndex > 0) {
                    loadChapter(currentChapterIndex - 1);
                }
            } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
                if (currentChapterIndex < chapters.length - 1) {
                    loadChapter(currentChapterIndex + 1);
                }
            } else if (e.key === 'b' || e.key === 'B') {
                if (!e.ctrlKey && !e.metaKey) {
                    showBookmarkModal();
                }
            } else if (e.key === 'Escape') {
                closeAllSidebars();
                closeBookmarkModal();
            }
        });
        
        document.getElementById('closeBookmarkModalBtn').addEventListener('click', closeBookmarkModal);
        document.getElementById('cancelBookmarkBtn').addEventListener('click', closeBookmarkModal);
        document.getElementById('saveBookmarkBtn').addEventListener('click', saveBookmark);
    }
});
