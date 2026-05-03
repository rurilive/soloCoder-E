document.addEventListener('DOMContentLoaded', function() {
    const bookId = window.bookId;
    
    let currentChapterIndex = 0;
    let chapters = [];
    let currentChapterId = null;
    let fontSize = 16;
    let lineHeight = 1.8;
    let currentTheme = 'light';
    let readingMode = 'chapter';
    let fullContentLoaded = false;
    let fontFamily = 'system';
    let fontColor = '#333333';
    let paginationMode = 'scroll';
    let currentPage = 1;
    let totalPages = 1;
    let pages = [];
    let currentChapterContent = '';
    
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
        const savedReadingMode = localStorage.getItem('ereader_readingMode');
        const savedFontFamily = localStorage.getItem('ereader_fontFamily');
        const savedFontColor = localStorage.getItem('ereader_fontColor');
        const savedPaginationMode = localStorage.getItem('ereader_paginationMode');
        
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
        
        if (savedReadingMode) {
            readingMode = savedReadingMode;
            updateReadingModeUI();
        }
        
        if (savedFontFamily) {
            fontFamily = savedFontFamily;
            updateFontFamily();
        }
        
        if (savedFontColor) {
            fontColor = savedFontColor;
            updateFontColor();
        }
        
        if (savedPaginationMode) {
            paginationMode = savedPaginationMode;
            updatePaginationModeUI();
        }
    }
    
    function loadBook() {
        fetch(`/books/${bookId}`)
            .then(response => response.json())
            .then(book => {
                chapters = book.chapters;
                renderTOC();
                
                if (chapters.length > 0) {
                    if (readingMode === 'full') {
                        loadFullContent();
                    } else {
                        loadChapter(0);
                    }
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
                currentChapterContent = chapterData.content;
                
                if (paginationMode === 'page') {
                    paginateContent(currentChapterContent);
                    currentPage = 1;
                    renderPage();
                } else {
                    const pageContent = document.getElementById('pageContent');
                    pageContent.innerHTML = formatContent(currentChapterContent);
                }
                
                document.getElementById('currentChapterTitle').textContent = chapter.title;
                
                updateChapterButtons();
                highlightCurrentTOC();
                
                if (scrollToTop && paginationMode === 'scroll') {
                    const pageContent = document.getElementById('pageContent');
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
    
    function paginateContent(content) {
        const pageContent = document.getElementById('pageContent');
        const containerHeight = pageContent.clientHeight - 40;
        const charPerPage = Math.floor(containerHeight * (fontSize / 20) * 1.5);
        
        const formattedContent = formatContent(content);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = formattedContent;
        const textContent = tempDiv.textContent || tempDiv.innerText;
        
        pages = [];
        let currentPageContent = '';
        let charCount = 0;
        
        const paragraphs = content.split('\n\n');
        
        paragraphs.forEach(paragraph => {
            const trimmed = paragraph.trim();
            if (!trimmed) return;
            
            const paraLength = trimmed.length;
            
            if (charCount + paraLength > charPerPage && charCount > 0) {
                pages.push(currentPageContent);
                currentPageContent = `<p>${escapeHtml(trimmed)}</p>`;
                charCount = paraLength;
            } else {
                currentPageContent += `<p>${escapeHtml(trimmed)}</p>`;
                charCount += paraLength;
            }
        });
        
        if (currentPageContent) {
            pages.push(currentPageContent);
        }
        
        totalPages = pages.length || 1;
        updatePageInfo();
    }
    
    function renderPage() {
        if (paginationMode !== 'page' || pages.length === 0) return;
        
        const pageContent = document.getElementById('pageContent');
        const pageIndex = currentPage - 1;
        
        if (pageIndex >= 0 && pageIndex < pages.length) {
            pageContent.innerHTML = pages[pageIndex];
        }
        
        updatePageInfo();
        updatePageButtons();
    }
    
    function updatePageInfo() {
        const pageInfo = document.getElementById('pageInfo');
        if (pageInfo) {
            pageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页`;
        }
    }
    
    function updatePageButtons() {
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        
        if (prevPageBtn) {
            prevPageBtn.disabled = currentPage <= 1;
            prevPageBtn.style.opacity = currentPage <= 1 ? '0.5' : '1';
        }
        
        if (nextPageBtn) {
            nextPageBtn.disabled = currentPage >= totalPages;
            nextPageBtn.style.opacity = currentPage >= totalPages ? '0.5' : '1';
        }
    }
    
    function goToPage(pageNum) {
        if (paginationMode !== 'page') return;
        if (pageNum < 1 || pageNum > totalPages) return;
        
        currentPage = pageNum;
        renderPage();
    }
    
    function prevPage() {
        if (currentPage > 1) {
            goToPage(currentPage - 1);
        } else if (currentChapterIndex > 0) {
            loadChapter(currentChapterIndex - 1);
            if (paginationMode === 'page') {
                currentPage = totalPages;
                renderPage();
            }
        }
    }
    
    function nextPage() {
        if (currentPage < totalPages) {
            goToPage(currentPage + 1);
        } else if (currentChapterIndex < chapters.length - 1) {
            loadChapter(currentChapterIndex + 1);
        }
    }
    
    function loadFullContent() {
        if (fullContentLoaded && readingMode === 'full') {
            return;
        }
        
        fetch(`/books/${bookId}/raw-content`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.content) {
                    throw new Error('Invalid data format');
                }
                
                const pageContent = document.getElementById('pageContent');
                
                if (paginationMode === 'page') {
                    currentChapterContent = data.content;
                    paginateContent(data.content);
                    currentPage = 1;
                    renderPage();
                } else {
                    pageContent.innerHTML = formatRawContent(data.content);
                }
                
                document.getElementById('currentChapterTitle').textContent = data.title || '全文阅读';
                
                updateReadingModeClass('full');
                
                fullContentLoaded = true;
                if (paginationMode === 'scroll') {
                    pageContent.scrollTop = 0;
                    updateProgress();
                }
            })
            .catch(error => {
                console.error('Error loading raw content:', error);
                showMessage('加载原文失败', 'error');
            });
    }
    
    function formatRawContent(content) {
        if (!content) {
            return '<pre class="raw-content">暂无内容</pre>';
        }
        return `<pre class="raw-content">${escapeHtml(content)}</pre>`;
    }
    
    function updateReadingModeUI() {
        document.querySelectorAll('.reading-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === readingMode);
        });
        
        if (readingMode === 'full') {
            updateReadingModeClass('full');
        } else {
            updateReadingModeClass('chapter');
        }
    }
    
    function updateReadingModeClass(mode) {
        const body = document.body;
        body.classList.remove('reading-mode-full', 'reading-mode-chapter');
        body.classList.add(`reading-mode-${mode}`);
    }
    
    function toggleReadingMode(newMode) {
        if (newMode === readingMode) {
            return;
        }
        
        readingMode = newMode;
        localStorage.setItem('ereader_readingMode', readingMode);
        updateReadingModeUI();
        closeAllSidebars();
        
        if (newMode === 'full') {
            loadFullContent();
        } else {
            loadChapter(currentChapterIndex);
            updateReadingModeClass('chapter');
        }
    }
    
    function updatePaginationModeUI() {
        document.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === paginationMode);
        });
        
        const paginationControls = document.getElementById('paginationControls');
        const scrollControls = document.getElementById('scrollControls');
        
        if (paginationMode === 'page') {
            if (paginationControls) paginationControls.style.display = 'flex';
            if (scrollControls) scrollControls.style.display = 'none';
            
            if (currentChapterContent) {
                paginateContent(currentChapterContent);
                currentPage = 1;
                renderPage();
            }
        } else {
            if (paginationControls) paginationControls.style.display = 'none';
            if (scrollControls) scrollControls.style.display = 'flex';
            
            if (currentChapterContent) {
                const pageContent = document.getElementById('pageContent');
                pageContent.innerHTML = formatContent(currentChapterContent);
                updateProgress();
            }
        }
    }
    
    function togglePaginationMode(newMode) {
        if (newMode === paginationMode) {
            return;
        }
        
        paginationMode = newMode;
        localStorage.setItem('ereader_paginationMode', paginationMode);
        updatePaginationModeUI();
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
            const level = chapter.level || 0;
            const indentClass = `toc-level-${level}`;
            
            item.className = `toc-item ${indentClass}`;
            item.dataset.index = index;
            item.dataset.level = level;
            item.innerHTML = `
                <div class="toc-title">${escapeHtml(chapter.title)}</div>
                <div class="toc-order">第 ${index + 1} 章</div>
            `;
            
            item.addEventListener('click', () => {
                if (readingMode === 'full') {
                    currentChapterIndex = index;
                    toggleReadingMode('chapter');
                    setTimeout(() => {
                        loadChapter(index);
                    }, 100);
                } else {
                    loadChapter(index);
                }
                closeAllSidebars();
            });
            
            tocContent.appendChild(item);
        });
    }
    
    function scrollToChapter(index) {
        const chapterElement = document.querySelector(`.full-content-chapter[data-chapter-index="${index}"]`);
        if (chapterElement) {
            const pageContent = document.getElementById('pageContent');
            const offsetTop = chapterElement.offsetTop - 20;
            pageContent.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
            currentChapterIndex = index;
            highlightCurrentTOC();
        }
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
                <div class="bookmark-info" data-chapter-id="${bookmark.chapter_id}" data-position="${bookmark.position}">
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
                    loadChapter(chapterIndex, false);
                    
                    setTimeout(() => {
                        if (paginationMode === 'scroll' && bookmark.position > 0) {
                            const pageContent = document.getElementById('pageContent');
                            pageContent.scrollTop = bookmark.position;
                            updateProgress();
                        }
                    }, 300);
                    
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
        if (paginationMode === 'page') return;
        
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
        
        if (paginationMode === 'page' && currentChapterContent) {
            paginateContent(currentChapterContent);
            currentPage = 1;
            renderPage();
        }
    }
    
    function updateLineHeight() {
        const pageContent = document.getElementById('pageContent');
        pageContent.style.lineHeight = lineHeight;
        document.getElementById('lineHeightValue').textContent = lineHeight.toFixed(1);
        localStorage.setItem('ereader_lineHeight', lineHeight);
        
        if (paginationMode === 'page' && currentChapterContent) {
            paginateContent(currentChapterContent);
            currentPage = 1;
            renderPage();
        }
    }
    
    function updateFontFamily() {
        const pageContent = document.getElementById('pageContent');
        
        if (fontFamily === 'system') {
            pageContent.style.fontFamily = '';
        } else {
            pageContent.style.fontFamily = `"${fontFamily}", system-ui, -apple-system, sans-serif`;
        }
        
        const fontSelect = document.getElementById('fontSelect');
        if (fontSelect) {
            fontSelect.value = fontFamily;
        }
        
        localStorage.setItem('ereader_fontFamily', fontFamily);
        
        if (paginationMode === 'page' && currentChapterContent) {
            paginateContent(currentChapterContent);
            currentPage = 1;
            renderPage();
        }
    }
    
    function updateFontColor() {
        const pageContent = document.getElementById('pageContent');
        pageContent.style.color = fontColor;
        
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.color === fontColor);
        });
        
        const customColorPicker = document.getElementById('customColorPicker');
        if (customColorPicker) {
            customColorPicker.value = fontColor;
        }
        
        localStorage.setItem('ereader_fontColor', fontColor);
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
        let position = pageContent.scrollTop;
        
        if (paginationMode === 'page') {
            position = currentPage;
        }
        
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
        
        document.querySelectorAll('.reading-mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const newMode = btn.dataset.mode;
                toggleReadingMode(newMode);
            });
        });
        
        const fontSelect = document.getElementById('fontSelect');
        if (fontSelect) {
            fontSelect.addEventListener('change', (e) => {
                fontFamily = e.target.value;
                updateFontFamily();
            });
        }
        
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                fontColor = btn.dataset.color;
                updateFontColor();
            });
        });
        
        const customColorPicker = document.getElementById('customColorPicker');
        if (customColorPicker) {
            customColorPicker.addEventListener('input', (e) => {
                fontColor = e.target.value;
                updateFontColor();
            });
        }
        
        document.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const newMode = btn.dataset.mode;
                togglePaginationMode(newMode);
            });
        });
        
        const prevPageBtn = document.getElementById('prevPageBtn');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', prevPage);
        }
        
        const nextPageBtn = document.getElementById('nextPageBtn');
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', nextPage);
        }
        
        const pageContent = document.getElementById('pageContent');
        pageContent.addEventListener('scroll', updateProgress);
        
        const progressSlider = document.getElementById('progressSlider');
        progressSlider.addEventListener('input', (e) => {
            if (paginationMode === 'page') return;
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
                if (paginationMode === 'page') {
                    prevPage();
                } else if (currentChapterIndex > 0) {
                    if (readingMode === 'full') {
                        currentChapterIndex = currentChapterIndex - 1;
                        toggleReadingMode('chapter');
                        setTimeout(() => {
                            loadChapter(currentChapterIndex);
                        }, 100);
                    } else {
                        loadChapter(currentChapterIndex - 1);
                    }
                }
            } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
                if (paginationMode === 'page') {
                    nextPage();
                } else if (currentChapterIndex < chapters.length - 1) {
                    if (readingMode === 'full') {
                        currentChapterIndex = currentChapterIndex + 1;
                        toggleReadingMode('chapter');
                        setTimeout(() => {
                            loadChapter(currentChapterIndex);
                        }, 100);
                    } else {
                        loadChapter(currentChapterIndex + 1);
                    }
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
