// Analyze page functionality

class AnalyzeManager {
    constructor() {
        this.currentStep = 1;
        this.processedUrls = [];
        this.selectedUrls = [];
        this.selectedUrlIndices = new Set(); // Track selected URL indices across pages
        this.summarySettings = {
            length: 'brief',
            tone: 'neutral',
            format: 'prose',
            model: 'gpt-3.5-turbo',
            customWordCount: 250
        };
        
        // Pagination state
        this.pagination = {
            currentPage: 1,
            urlsPerPage: 50,
            totalUrls: 0,
            totalPages: 0
        };
        
        this.initializeEventListeners();
        this.loadUserDefaults();
    }
    
    initializeEventListeners() {
        // Input method selection
        document.querySelectorAll('.input-method').forEach(method => {
            method.addEventListener('click', () => this.selectInputMethod(method));
        });
        
        // File upload
        document.getElementById('file-input').addEventListener('change', this.handleFileUpload.bind(this));
        
        // RSS fetch
        document.getElementById('rss-fetch').addEventListener('click', this.fetchRssUrls.bind(this));
        
        // Process URLs
        document.getElementById('process-urls').addEventListener('click', this.processUrls.bind(this));
        
        // Save URLs for later
        document.getElementById('save-urls').addEventListener('click', this.saveUrlsForLater.bind(this));
        
        // Navigation
        document.getElementById('back-to-step-1').addEventListener('click', () => this.showStep(1));
        document.getElementById('proceed-to-settings').addEventListener('click', () => this.showStep(3));
        document.getElementById('back-to-step-2').addEventListener('click', () => this.showStep(2));
        
        // URL selection
        document.getElementById('select-all').addEventListener('change', this.toggleSelectAll.bind(this));
        
        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => this.goToPage(this.pagination.currentPage - 1));
        document.getElementById('next-page').addEventListener('click', () => this.goToPage(this.pagination.currentPage + 1));
        
        // Settings
        document.querySelectorAll('input[name="length"]').forEach(radio => {
            radio.addEventListener('change', this.handleLengthChange.bind(this));
        });
        
        document.getElementById('word-count-slider').addEventListener('input', this.updateWordCountDisplay.bind(this));
        
        // Generate summaries
        document.getElementById('generate-summaries').addEventListener('click', this.generateSummaries.bind(this));
        
        // Results actions
        document.getElementById('analyze-more').addEventListener('click', () => this.resetToStep1());
        document.getElementById('save-all').addEventListener('click', this.saveAllSummaries.bind(this));
    }
    
    selectInputMethod(selectedMethod) {
        // Remove active class from all methods
        document.querySelectorAll('.input-method').forEach(method => {
            method.classList.remove('active');
        });
        
        // Add active class to selected method
        selectedMethod.classList.add('active');
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        document.getElementById('file-name').textContent = file.name;
        
        try {
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            // Handle bookmark files differently
            if (fileExtension === 'html' || fileExtension === 'htm') {
                await this.handleBookmarkFile(file);
            } else {
                // Handle regular text/CSV files
                const content = await this.readFileContent(file);
                
                const response = await AppUtils.apiRequest('/api/process-urls', {
                    method: 'POST',
                    body: JSON.stringify({
                        content: content,
                        type: fileExtension
                    })
                });
                
                this.displayProcessedUrls(response.urls);
                AppUtils.showNotification(`Processed ${response.total} URLs from file`, 'success');
            }
            
        } catch (error) {
            AppUtils.showNotification('Failed to process file: ' + error.message, 'error');
        }
    }
    
    readFileContent(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }
    
    async fetchRssUrls() {
        const rssUrl = document.getElementById('rss-input').value.trim();
        if (!rssUrl) {
            AppUtils.showNotification('Please enter an RSS feed URL', 'warning');
            return;
        }
        
        try {
            AppUtils.showLoading('Fetching RSS feed...');
            
            const response = await AppUtils.apiRequest('/api/process-urls', {
                method: 'POST',
                body: JSON.stringify({
                    rss_url: rssUrl
                })
            });
            
            this.displayProcessedUrls(response.urls);
            AppUtils.showNotification(`Found ${response.total} articles in RSS feed`, 'success');
            
        } catch (error) {
            AppUtils.showNotification('Failed to fetch RSS feed: ' + error.message, 'error');
        } finally {
            AppUtils.hideLoading();
        }
    }
    
    async processUrls() {
        const urlText = document.getElementById('url-textarea').value.trim();
        if (!urlText) {
            AppUtils.showNotification('Please enter some URLs', 'warning');
            return;
        }
        
        const urls = urlText.split('\n').map(url => url.trim()).filter(url => url);
        
        if (urls.length === 0) {
            AppUtils.showNotification('No valid URLs found', 'warning');
            return;
        }
        
        try {
            AppUtils.showLoading('Processing URLs...');
            
            const response = await AppUtils.apiRequest('/api/process-urls', {
                method: 'POST',
                body: JSON.stringify({ urls })
            });
            
            this.processedUrls = response.urls;
            this.displayProcessedUrls(response.urls);
            this.showStep(2);
            
            AppUtils.showNotification(`Processed ${response.total} URLs`, 'success');
            
        } catch (error) {
            AppUtils.showNotification('Failed to process URLs: ' + error.message, 'error');
        } finally {
            AppUtils.hideLoading();
        }
    }
    
    displayProcessedUrls(urls) {
        // Store all URLs and setup pagination
        this.processedUrls = urls;
        this.selectedUrlIndices.clear(); // Reset selection tracking
        this.pagination.totalUrls = urls.length;
        this.pagination.totalPages = Math.ceil(urls.length / this.pagination.urlsPerPage);
        this.pagination.currentPage = 1;
        
        // Show pagination if needed
        const paginationContainer = document.getElementById('url-pagination');
        if (urls.length > this.pagination.urlsPerPage) {
            paginationContainer.style.display = 'block';
            this.updatePaginationUI();
        } else {
            paginationContainer.style.display = 'none';
        }
        
        // Display current page
        this.displayCurrentPage();
    }
    
    displayCurrentPage() {
        const urlList = document.getElementById('url-list');
        urlList.innerHTML = '';
        
        // Calculate pagination bounds
        const startIndex = (this.pagination.currentPage - 1) * this.pagination.urlsPerPage;
        const endIndex = Math.min(startIndex + this.pagination.urlsPerPage, this.processedUrls.length);
        const currentPageUrls = this.processedUrls.slice(startIndex, endIndex);
        
        currentPageUrls.forEach((urlData, localIndex) => {
            const globalIndex = startIndex + localIndex;
            const urlItem = document.createElement('div');
            urlItem.className = 'url-item';
            
            urlItem.innerHTML = `
                <input type="checkbox" class="url-checkbox" data-index="${globalIndex}" 
                       ${urlData.accessible ? '' : 'disabled'}>
                <div class="url-info">
                    <div class="url-title">${urlData.title}</div>
                    <a href="${urlData.url}" target="_blank" class="url-link">${urlData.url}</a>
                </div>
                <div class="url-status ${urlData.status}">${urlData.accessible ? 'Accessible' : 'Error'}</div>
            `;
            
            urlList.appendChild(urlItem);
        });
        
        // Add event listeners to checkboxes and restore selection state
        document.querySelectorAll('.url-checkbox').forEach(checkbox => {
            const index = parseInt(checkbox.dataset.index);
            // Restore selection state from our tracking
            checkbox.checked = this.selectedUrlIndices.has(index);
            checkbox.addEventListener('change', this.handleUrlSelection.bind(this));
        });
        
        this.updateSelectionCount();
        this.updateSelectAllState();
        this.updatePaginationUI();
    }
    
    updatePaginationUI() {
        // Update pagination info text
        const startIndex = (this.pagination.currentPage - 1) * this.pagination.urlsPerPage + 1;
        const endIndex = Math.min(this.pagination.currentPage * this.pagination.urlsPerPage, this.pagination.totalUrls);
        
        document.getElementById('pagination-info-text').textContent = 
            `Showing ${startIndex}-${endIndex} of ${this.pagination.totalUrls} URLs`;
        
        // Update prev/next buttons
        document.getElementById('prev-page').disabled = this.pagination.currentPage === 1;
        document.getElementById('next-page').disabled = this.pagination.currentPage === this.pagination.totalPages;
        
        // Update page numbers
        this.updatePageNumbers();
    }
    
    updatePageNumbers() {
        const pagesContainer = document.getElementById('pagination-pages');
        pagesContainer.innerHTML = '';
        
        const currentPage = this.pagination.currentPage;
        const totalPages = this.pagination.totalPages;
        
        // Show up to 5 page numbers with smart truncation
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);
        
        // Adjust range if we're near the beginning or end
        if (currentPage <= 3) {
            endPage = Math.min(5, totalPages);
        }
        if (currentPage >= totalPages - 2) {
            startPage = Math.max(1, totalPages - 4);
        }
        
        // Add first page and ellipsis if needed
        if (startPage > 1) {
            this.addPageButton(1, pagesContainer);
            if (startPage > 2) {
                const ellipsis = document.createElement('span');
                ellipsis.textContent = '...';
                ellipsis.style.padding = '0.5rem';
                pagesContainer.appendChild(ellipsis);
            }
        }
        
        // Add page numbers
        for (let i = startPage; i <= endPage; i++) {
            this.addPageButton(i, pagesContainer);
        }
        
        // Add last page and ellipsis if needed
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement('span');
                ellipsis.textContent = '...';
                ellipsis.style.padding = '0.5rem';
                pagesContainer.appendChild(ellipsis);
            }
            this.addPageButton(totalPages, pagesContainer);
        }
    }
    
    addPageButton(pageNum, container) {
        const button = document.createElement('button');
        button.className = `page-btn ${pageNum === this.pagination.currentPage ? 'active' : ''}`;
        button.textContent = pageNum;
        button.addEventListener('click', () => this.goToPage(pageNum));
        container.appendChild(button);
    }
    
    goToPage(pageNum) {
        if (pageNum < 1 || pageNum > this.pagination.totalPages || pageNum === this.pagination.currentPage) {
            return;
        }
        
        this.pagination.currentPage = pageNum;
        this.displayCurrentPage();
    }
    
    toggleSelectAll() {
        const selectAll = document.getElementById('select-all');
        const checkboxes = document.querySelectorAll('.url-checkbox:not([disabled])');
        
        if (selectAll.checked) {
            // Select all accessible URLs across all pages
            this.processedUrls.forEach((urlData, index) => {
                if (urlData.accessible) {
                    this.selectedUrlIndices.add(index);
                }
            });
        } else {
            // Deselect all URLs
            this.selectedUrlIndices.clear();
        }
        
        // Update current page checkboxes
        checkboxes.forEach(checkbox => {
            const index = parseInt(checkbox.dataset.index);
            checkbox.checked = this.selectedUrlIndices.has(index);
        });
        
        this.updateSelectionCount();
    }
    
    handleUrlSelection(event) {
        const checkbox = event.target;
        const index = parseInt(checkbox.dataset.index);
        
        if (checkbox.checked) {
            this.selectedUrlIndices.add(index);
        } else {
            this.selectedUrlIndices.delete(index);
        }
        
        this.updateSelectionCount();
        this.updateSelectAllState();
    }
    
    updateSelectionCount() {
        const count = this.selectedUrlIndices.size;
        
        document.querySelector('.selection-count').textContent = `${count} selected`;
        
        // Update proceed button state
        const proceedButton = document.getElementById('proceed-to-settings');
        proceedButton.disabled = count === 0;
    }
    
    updateSelectAllState() {
        const selectAll = document.getElementById('select-all');
        const totalAccessibleUrls = this.processedUrls.filter(url => url.accessible).length;
        const selectedCount = this.selectedUrlIndices.size;
        
        if (selectedCount === 0) {
            selectAll.checked = false;
            selectAll.indeterminate = false;
        } else if (selectedCount === totalAccessibleUrls) {
            selectAll.checked = true;
            selectAll.indeterminate = false;
        } else {
            selectAll.checked = false;
            selectAll.indeterminate = true;
        }
    }
    
    handleLengthChange(event) {
        const value = event.target.value;
        const customLength = document.getElementById('custom-length');
        
        if (value === 'custom') {
            customLength.style.display = 'block';
        } else {
            customLength.style.display = 'none';
        }
        
        this.summarySettings.length = value;
    }
    
    updateWordCountDisplay() {
        const slider = document.getElementById('word-count-slider');
        const display = document.getElementById('word-count-display');
        
        display.textContent = slider.value;
        this.summarySettings.customWordCount = parseInt(slider.value);
    }
    
    async generateSummaries() {
        // Get selected URLs from our tracking set
        this.selectedUrls = Array.from(this.selectedUrlIndices).map(index => {
            return this.processedUrls[index];
        });
        
        if (this.selectedUrls.length === 0) {
            AppUtils.showNotification('Please select at least one URL', 'warning');
            return;
        }
        
        // Get settings
        this.summarySettings.tone = document.getElementById('tone-select').value;
        this.summarySettings.format = document.getElementById('format-select').value;
        this.summarySettings.model = document.getElementById('model-select').value;
        
        try {
            AppUtils.showLoading('Extracting articles and generating summaries...');
            
            const summaries = [];
            
            for (let i = 0; i < this.selectedUrls.length; i++) {
                const urlData = this.selectedUrls[i];
                
                AppUtils.showLoading(`Processing article ${i + 1} of ${this.selectedUrls.length}...`);
                
                // Extract article content
                const extractResponse = await AppUtils.apiRequest('/api/extract-article', {
                    method: 'POST',
                    body: JSON.stringify({ url: urlData.url })
                });
                
                if (extractResponse.error || !extractResponse.content) {
                    summaries.push({
                        url: urlData.url,
                        title: urlData.title,
                        error: extractResponse.error || 'Failed to extract content',
                        is_paywalled: extractResponse.is_paywalled,
                        allow_manual_input: extractResponse.is_paywalled
                    });
                    continue;
                }
                
                // Generate summary
                const summaryResponse = await AppUtils.apiRequest('/api/generate-summary', {
                    method: 'POST',
                    body: JSON.stringify({
                        content: extractResponse.content,
                        url: urlData.url,
                        title: extractResponse.title,
                        author: extractResponse.author,
                        publication_date: extractResponse.publication_date,
                        ...this.summarySettings
                    })
                });
                
                summaries.push(summaryResponse.summary);
            }
            
            this.displaySummaries(summaries);
            this.showStep(4);
            
            AppUtils.showNotification('Summaries generated successfully!', 'success');
            
        } catch (error) {
            AppUtils.showNotification('Failed to generate summaries: ' + error.message, 'error');
        } finally {
            AppUtils.hideLoading();
        }
    }
    
    displaySummaries(summaries) {
        const container = document.getElementById('summaries-container');
        container.innerHTML = '';
        
        summaries.forEach(summary => {
            const summaryElement = document.createElement('div');
            summaryElement.className = 'summary-result';
            
            if (summary.error) {
                const manualInputOption = summary.allow_manual_input ? `
                    <div class="manual-input-option" style="margin-top: 1rem;">
                        <p style="color: #6b7280; margin-bottom: 0.5rem;">You can manually paste the article content:</p>
                        <textarea class="manual-text-input" placeholder="Paste article content here..." style="width: 100%; height: 100px; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.5rem;"></textarea>
                        <button class="btn btn-secondary" onclick="retryWithManualInput('${summary.url}', '${summary.title}', this)" style="margin-top: 0.5rem;">Generate Summary</button>
                    </div>
                ` : '';
                
                summaryElement.innerHTML = `
                    <div class="summary-result-header">
                        <div class="summary-result-meta">
                            <div class="summary-result-title">${summary.title}</div>
                            <a href="${summary.url}" target="_blank" class="summary-result-url">${summary.url}</a>
                        </div>
                    </div>
                    <div class="summary-result-error">
                        <p style="color: #dc2626;">Error: ${summary.error}</p>
                        ${manualInputOption}
                    </div>
                `;
            } else {
                summaryElement.innerHTML = `
                    <div class="summary-result-header">
                        <div class="summary-result-meta">
                            <div class="summary-result-title">${summary.metadata.title}</div>
                            <a href="${summary.metadata.url}" target="_blank" class="summary-result-url">${summary.metadata.url}</a>
                            ${summary.metadata.author ? `<div class="summary-result-author">by ${summary.metadata.author}</div>` : ''}
                        </div>
                        <div class="summary-result-settings">
                            <span class="setting-tag">${summary.settings.length}</span>
                            <span class="setting-tag">${summary.settings.tone}</span>
                            <span class="setting-tag">${summary.settings.format}</span>
                            <span class="setting-tag">${summary.word_count} words</span>
                        </div>
                    </div>
                    <div class="summary-result-text">${summary.text.replace(/\n/g, '<br>')}</div>
                    <div class="summary-result-actions">
                        <button class="btn btn-secondary" onclick="navigator.clipboard.writeText('${summary.text.replace(/'/g, "\\'")}')">Copy</button>
                        <a href="/summary/${summary.id}" class="btn btn-primary">View Details</a>
                    </div>
                `;
            }
            
            container.appendChild(summaryElement);
        });
    }
    
    showStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.analyze-step').forEach(step => {
            step.style.display = 'none';
        });
        
        // Show selected step
        document.getElementById(`step-${stepNumber}`).style.display = 'block';
        this.currentStep = stepNumber;
        
        // Scroll to top
        window.scrollTo(0, 0);
    }
    
    resetToStep1() {
        this.processedUrls = [];
        this.selectedUrls = [];
        this.selectedUrlIndices.clear();
        document.getElementById('url-textarea').value = '';
        document.getElementById('file-name').textContent = 'No file selected';
        document.getElementById('rss-input').value = '';
        this.showStep(1);
    }
    
    async saveAllSummaries() {
        AppUtils.showNotification('All summaries have been saved to your history!', 'success');
        
        // Redirect to history page after a short delay
        setTimeout(() => {
            window.location.href = '/history';
        }, 2000);
    }
    
    async saveUrlsForLater() {
        const urlText = document.getElementById('url-textarea').value.trim();
        if (!urlText) {
            AppUtils.showNotification('Please enter some URLs to save', 'warning');
            return;
        }
        
        const urls = urlText.split('\n').map(url => url.trim()).filter(url => url);
        
        if (urls.length === 0) {
            AppUtils.showNotification('No valid URLs found', 'warning');
            return;
        }
        
        try {
            AppUtils.showLoading('Saving URLs...');
            
            let savedCount = 0;
            let skippedCount = 0;
            
            for (const url of urls) {
                try {
                    await AppUtils.apiRequest('/api/save-url', {
                        method: 'POST',
                        body: JSON.stringify({ url })
                    });
                    savedCount++;
                } catch (error) {
                    if (error.message.includes('already saved')) {
                        skippedCount++;
                    } else {
                        throw error;
                    }
                }
            }
            
            const message = `Saved ${savedCount} URLs` + (skippedCount > 0 ? ` (${skippedCount} already saved)` : '');
            AppUtils.showNotification(message, 'success');
            
            // Clear the textarea
            document.getElementById('url-textarea').value = '';
            
        } catch (error) {
            AppUtils.showNotification('Failed to save URLs: ' + error.message, 'error');
        } finally {
            AppUtils.hideLoading();
        }
    }
    
    async handleBookmarkFile(file) {
        try {
            AppUtils.showLoading('Parsing bookmark file...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/upload-bookmarks', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Failed to parse bookmark file');
            }
            
            // Display parsed URLs
            this.processedUrls = result.urls;
            this.displayProcessedUrls(result.urls);
            this.showStep(2);
            
            // Show summary of bookmark parsing
            let message = `Found ${result.total_bookmarks} bookmarks, processed ${result.processed_count} URLs`;
            if (result.folders_found && result.folders_found.length > 0) {
                message += `\nFolders found: ${result.folders_found.slice(0, 3).join(', ')}`;
                if (result.folders_found.length > 3) {
                    message += ` and ${result.folders_found.length - 3} more`;
                }
            }
            
            AppUtils.showNotification(message, 'success');
            
        } catch (error) {
            AppUtils.showNotification('Failed to parse bookmark file: ' + error.message, 'error');
        } finally {
            AppUtils.hideLoading();
        }
    }
    
    async loadUserDefaults() {
        // Load user's default settings
        // This would typically be done via an API call
        // For now, we'll use the defaults set in the HTML
    }
}

// Global function for manual input retry
async function retryWithManualInput(url, title, buttonElement) {
    const textarea = buttonElement.parentElement.querySelector('.manual-text-input');
    const manualText = textarea.value.trim();
    
    if (!manualText) {
        AppUtils.showNotification('Please paste the article content first', 'warning');
        return;
    }
    
    try {
        AppUtils.showLoading('Generating summary from manual input...');
        
        // Generate summary with manual content
        const summaryResponse = await AppUtils.apiRequest('/api/generate-summary', {
            method: 'POST',
            body: JSON.stringify({
                content: manualText,
                url: url,
                title: title,
                length: analyzeManager.summarySettings.length,
                tone: analyzeManager.summarySettings.tone,
                format: analyzeManager.summarySettings.format,
                model: analyzeManager.summarySettings.model,
                custom_word_count: analyzeManager.summarySettings.customWordCount
            })
        });
        
        // Replace the error with the successful summary
        const resultElement = buttonElement.closest('.summary-result');
        resultElement.innerHTML = `
            <div class="summary-result-header">
                <div class="summary-result-meta">
                    <div class="summary-result-title">${summaryResponse.summary.metadata.title}</div>
                    <a href="${summaryResponse.summary.metadata.url}" target="_blank" class="summary-result-url">${summaryResponse.summary.metadata.url}</a>
                </div>
                <div class="summary-result-settings">
                    <span class="setting-tag">${summaryResponse.summary.settings.length}</span>
                    <span class="setting-tag">${summaryResponse.summary.settings.tone}</span>
                    <span class="setting-tag">${summaryResponse.summary.settings.format}</span>
                    <span class="setting-tag">${summaryResponse.summary.word_count} words</span>
                </div>
            </div>
            <div class="summary-result-text">${summaryResponse.summary.text.replace(/\n/g, '<br>')}</div>
            <div class="summary-result-actions">
                <button class="btn btn-secondary" onclick="navigator.clipboard.writeText('${summaryResponse.summary.text.replace(/'/g, "\\'")}')">Copy</button>
                <a href="/summary/${summaryResponse.summary.id}" class="btn btn-primary">View Details</a>
            </div>
        `;
        
        AppUtils.showNotification('Summary generated successfully!', 'success');
        
    } catch (error) {
        AppUtils.showNotification('Failed to generate summary: ' + error.message, 'error');
    } finally {
        AppUtils.hideLoading();
    }
}

// Global reference to the manager for access in global functions
let analyzeManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    analyzeManager = new AnalyzeManager();
});