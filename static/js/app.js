document.addEventListener('DOMContentLoaded', function() {
    initUploadArea();
    loadBooks();
});

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

        const formData = new FormData();
        formData.append('file', file);

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
                    showMessage(`书籍 "${response.title}" 上传成功！`, 'success');
                    loadBooks();
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

    fetch('/books/')
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

    card.innerHTML = `
        <div class="book-card-header">
            <h3>${escapeHtml(book.title)}</h3>
            <button class="delete-book-btn" data-id="${book.id}" title="删除书籍">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
        <p class="book-card-author">${escapeHtml(book.author || '未知作者')}</p>
        <div class="book-card-footer">
            <span class="book-type">${book.file_type.toUpperCase()}</span>
            <span class="book-date">最后阅读: ${lastReadDate}</span>
        </div>
    `;

    card.addEventListener('click', (e) => {
        if (!e.target.closest('.delete-book-btn')) {
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

// 添加动画样式
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
