let categories = [];
let currentEditingBookId = null;

document.addEventListener('DOMContentLoaded', function() {
    loadCategories().then(() => {
        initUploadArea();
        initCategoryFilter();
        initCategoryModal();
        loadBooks();
    });
});

function loadCategories() {
    return fetch('/categories/')
        .then(response => response.json())
        .then(data => {
            categories = data;
            populateCategorySelects();
            return data;
        })
        .catch(error => {
            console.error('Error loading categories:', error);
            showMessage('加载分类失败', 'error');
            return [];
        });
}

function populateCategorySelects() {
    const uploadSelect = document.getElementById('categorySelect');
    const filterSelect = document.getElementById('categoryFilter');
    const modalSelect = document.getElementById('modalCategorySelect');

    [uploadSelect, filterSelect, modalSelect].forEach(select => {
        if (select) {
            const currentValue = select.value;
            const isFilterSelect = select.id === 'categoryFilter';
            
            select.innerHTML = isFilterSelect 
                ? '<option value="">全部</option>' 
                : '<option value="">不分类</option>';
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                if (category.id == currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
    });
}

function initCategoryFilter() {
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', () => {
            loadBooks();
        });
    }
}

function initCategoryModal() {
    const modal = document.getElementById('categoryModal');
    const cancelBtn = document.getElementById('cancelCategoryBtn');
    const confirmBtn = document.getElementById('confirmCategoryBtn');

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            closeCategoryModal();
        });
    }

    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            const modalSelect = document.getElementById('modalCategorySelect');
            const categoryId = modalSelect.value ? parseInt(modalSelect.value) : null;
            updateBookCategory(currentEditingBookId, categoryId);
        });
    }

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeCategoryModal();
            }
        });
    }
}

function openCategoryModal(bookId, currentCategoryId) {
    currentEditingBookId = bookId;
    const modal = document.getElementById('categoryModal');
    const modalSelect = document.getElementById('modalCategorySelect');
    
    if (modalSelect) {
        modalSelect.value = currentCategoryId || '';
    }
    
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeCategoryModal() {
    currentEditingBookId = null;
    const modal = document.getElementById('categoryModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function updateBookCategory(bookId, categoryId) {
    fetch(`/books/${bookId}/category`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ category_id: categoryId })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            return response.json().then(data => {
                throw new Error(data.detail || '更新分类失败');
            });
        }
    })
    .then(data => {
        closeCategoryModal();
        showMessage(`已将 "${data.title}" 分类为: ${data.category_name || '未分类'}`, 'success');
        loadBooks();
    })
    .catch(error => {
        console.error('Error updating category:', error);
        showMessage(error.message || '更新分类失败', 'error');
    });
}

function initUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    function uploadFile(file) {
        const validExtensions = ['.epub', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validExtensions.includes(fileExtension)) {
            showMessage('只支持 .epub 和 .txt 格式的文件', 'error');
            return;
        }

        uploadProgress.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = '上传中...';

        const categorySelect = document.getElementById('categorySelect');
        const categoryId = categorySelect.value ? parseInt(categorySelect.value) : null;

        const formData = new FormData();
        formData.append('file', file);
        if (categoryId !== null) {
            formData.append('category_id', categoryId);
        }

        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressFill.style.width = percentComplete + '%';
                progressText.textContent = `上传中: ${Math.round(percentComplete)}%`;
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                progressText.textContent = '解析中...';
                progressFill.style.width = '100%';
                
                setTimeout(() => {
                    uploadProgress.style.display = 'none';
                    const categoryInfo = response.category_name ? ` (分类: ${response.category_name})` : '';
                    showMessage(`书籍 "${response.title}" 上传成功！${categoryInfo}`, 'success');
                    loadBooks();
                    loadCategories();
                }, 500);
            } else {
                const errorResponse = JSON.parse(xhr.responseText);
                uploadProgress.style.display = 'none';
                showMessage(errorResponse.detail || '上传失败', 'error');
            }
        });

        xhr.addEventListener('error', () => {
            uploadProgress.style.display = 'none';
            showMessage('网络错误，请重试', 'error');
        });

        xhr.open('POST', '/upload/');
        xhr.send(formData);
    }
}

function loadBooks() {
    const booksGrid = document.getElementById('booksGrid');
    const emptyState = document.getElementById('emptyState');
    const categoryFilter = document.getElementById('categoryFilter');
    
    let url = '/books/';
    if (categoryFilter && categoryFilter.value) {
        url += `?category_id=${categoryFilter.value}`;
    }

    fetch(url)
        .then(response => response.json())
        .then(books => {
            if (books.length === 0) {
                booksGrid.style.display = 'none';
                emptyState.style.display = 'block';
                return;
            }

            booksGrid.style.display = 'grid';
            emptyState.style.display = 'none';
            booksGrid.innerHTML = '';

            books.forEach(book => {
                const bookCard = createBookCard(book);
                booksGrid.appendChild(bookCard);
            });
        })
        .catch(error => {
            console.error('Error loading books:', error);
            showMessage('加载书籍列表失败', 'error');
        });
}

function createBookCard(book) {
    const card = document.createElement('div');
    card.className = 'book-card';
    
    const lastReadDate = book.last_read_at 
        ? new Date(book.last_read_at).toLocaleDateString('zh-CN')
        : '未阅读';

    const categoryName = book.category_name || '未分类';
    const categoryClass = book.category_name ? 'category-tag' : 'category-tag category-uncategorized';

    card.innerHTML = `
        <div class="book-card-header">
            <h3>${escapeHtml(book.title)}</h3>
            <div class="book-card-actions">
                <button class="category-btn" data-id="${book.id}" data-category="${book.category_id || ''}" title="修改分类">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button class="delete-book-btn" data-id="${book.id}" title="删除书籍">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        </div>
        <p class="book-card-author">${escapeHtml(book.author || '未知作者')}</p>
        <span class="${categoryClass}">${escapeHtml(categoryName)}</span>
        <div class="book-card-footer">
            <span class="book-type">${book.file_type.toUpperCase()}</span>
            <span class="book-date">最后阅读: ${lastReadDate}</span>
        </div>
    `;

    card.addEventListener('click', (e) => {
        if (!e.target.closest('.delete-book-btn') && !e.target.closest('.category-btn')) {
            window.location.href = `/reader/${book.id}`;
        }
    });

    const deleteBtn = card.querySelector('.delete-book-btn');
    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (confirm(`确定要删除书籍 "${book.title}" 吗？`)) {
            deleteBook(book.id);
        }
    });

    const categoryBtn = card.querySelector('.category-btn');
    categoryBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        openCategoryModal(book.id, book.category_id);
    });

    return card;
}

function deleteBook(bookId) {
    fetch(`/books/${bookId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            showMessage('书籍删除成功', 'success');
            loadBooks();
            loadCategories();
        } else {
            return response.json().then(data => {
                throw new Error(data.detail || '删除失败');
            });
        }
    })
    .catch(error => {
        console.error('Error deleting book:', error);
        showMessage(error.message || '删除失败', 'error');
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

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
