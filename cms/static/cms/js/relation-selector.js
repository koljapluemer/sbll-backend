class RelationSelector {
  constructor(config) {
    this.fieldName = config.fieldName;
    this.searchUrl = config.searchUrl;
    this.createUrl = config.createUrl;
    this.languages = config.languages;

    // State
    this.selected = config.initial || [];
    this.results = [];
    this.query = '';
    this.loading = false;
    this.isOpen = false;
    this.highlighted = 0;
    this.selectedLanguage = this.getStoredLanguage() || 'eng';
    this.submitting = false;

    // Debounce timer
    this.searchDebounce = null;

    // Get DOM elements
    this.selectedTableBody = document.getElementById(`selected-${this.fieldName}`);
    this.languageSelect = document.getElementById(`language-${this.fieldName}`);
    this.input = document.getElementById(`input-${this.fieldName}`);
    this.resultsContainer = document.getElementById(`results-${this.fieldName}`);
    this.btnSubmit = document.getElementById(`btn-submit-${this.fieldName}`);
    this.errorDiv = document.getElementById(`error-${this.fieldName}`);

    this.init();
  }

  init() {
    // Populate language dropdown
    this.renderLanguageOptions();

    // Set stored/default language
    this.languageSelect.value = this.selectedLanguage;
    this.onLanguageChange(); // Enable input if language selected

    // Initial render
    this.renderSelectedTable();

    // Attach event listeners
    this.languageSelect.addEventListener('change', () => this.onLanguageChange());
    this.input.addEventListener('input', () => this.handleInputChange());
    this.input.addEventListener('focus', () => this.handleInputFocus());
    this.input.addEventListener('keydown', (e) => this.handleInputKeydown(e));
    this.input.addEventListener('blur', () => setTimeout(() => this.handleInputBlur(), 200));
    this.btnSubmit.addEventListener('click', () => this.handleSubmit());
  }

  renderLanguageOptions() {
    this.languageSelect.innerHTML = '<option value="">Language...</option>';
    this.languages.forEach(lang => {
      const option = document.createElement('option');
      option.value = lang.id;
      option.textContent = `${lang.label} (${lang.id})`;
      this.languageSelect.appendChild(option);
    });
  }

  onLanguageChange() {
    this.selectedLanguage = this.languageSelect.value;

    if (this.selectedLanguage) {
      // Enable input
      this.input.disabled = false;
      this.input.focus();

      // Store preference
      this.storeLanguage(this.selectedLanguage);

      // Re-run search if there's content
      if (this.query) {
        this.search();
      }
    } else {
      // Disable input and submit
      this.input.disabled = true;
      this.btnSubmit.disabled = true;
      this.query = '';
      this.input.value = '';
      this.results = [];
      this.isOpen = false;
      this.renderSearchResults();
    }

    this.updateSubmitButton();
  }

  storeLanguage(languageIso) {
    try {
      document.cookie = `glossLanguage=${languageIso}; path=/; max-age=31536000`; // 1 year
    } catch (e) {
      console.warn('Could not store language preference:', e);
    }
  }

  getStoredLanguage() {
    const cookie = this.getCookie('glossLanguage');
    if (cookie && this.languages.find(lang => lang.id === cookie)) {
      return cookie;
    }
    return null;
  }

  handleInputChange() {
    this.query = this.input.value;

    // Clear error
    this.errorDiv.style.display = 'none';

    // Update submit button
    this.updateSubmitButton();

    // Debounce search
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => {
      this.search();
    }, 200);
  }

  handleInputFocus() {
    if (this.results.length > 0) {
      this.isOpen = true;
      this.renderSearchResults();
    }
  }

  handleInputBlur() {
    this.isOpen = false;
    this.renderSearchResults();
  }

  handleInputKeydown(e) {
    if (!this.isOpen) {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.handleSubmit();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.highlighted = Math.min(this.highlighted + 1, this.results.length - 1);
      this.renderSearchResults();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.highlighted = Math.max(this.highlighted - 1, 0);
      this.renderSearchResults();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.results[this.highlighted]) {
        this.prefillFromResult(this.results[this.highlighted]);
      } else {
        this.handleSubmit();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.closeSearchResults();
    }
  }

  updateSubmitButton() {
    const hasContent = this.query.trim().length > 0;
    const hasLanguage = this.selectedLanguage !== '';
    this.btnSubmit.disabled = !hasContent || !hasLanguage || this.submitting;
  }

  async search() {
    const term = this.query.trim();

    if (!term || !this.selectedLanguage) {
      this.results = [];
      this.isOpen = false;
      this.renderSearchResults();
      return;
    }

    this.loading = true;
    this.isOpen = true;
    this.renderSearchResults();

    try {
      const params = new URLSearchParams({
        q: term,
        language: this.selectedLanguage
      });

      const response = await fetch(`${this.searchUrl}?${params}`, {
        credentials: 'same-origin'
      });
      const data = await response.json();
      this.results = data.results || [];
      this.highlighted = 0;
    } catch (error) {
      console.error('Search failed:', error);
      this.results = [];
    } finally {
      this.loading = false;
      this.renderSearchResults();
    }
  }

  renderSearchResults() {
    if (!this.isOpen) {
      this.resultsContainer.style.display = 'none';
      return;
    }

    this.resultsContainer.style.display = 'block';

    if (this.loading) {
      this.resultsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-light">Searching...</div>';
      return;
    }

    if (this.results.length === 0) {
      this.resultsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-light">No matches. Click Attach to create new.</div>';
      return;
    }

    this.resultsContainer.innerHTML = this.results.map((item, idx) => `
      <button
        type="button"
        class="w-full text-left px-3 py-2 hover:bg-base-200 flex justify-between items-center ${idx === this.highlighted ? 'bg-base-200' : ''}"
        data-prefill-id="${item.id}"
      >
        <span>${this.escapeHtml(item.content)}</span>
        <span class="badge badge-ghost">${this.escapeHtml(item.language_iso)}</span>
      </button>
    `).join('');

    // Attach prefill listeners
    this.resultsContainer.querySelectorAll('[data-prefill-id]').forEach((btn, idx) => {
      btn.addEventListener('click', () => {
        const item = this.results[idx];
        if (item) this.prefillFromResult(item);
      });
      btn.addEventListener('mouseenter', () => {
        this.highlighted = idx;
        this.renderSearchResults();
      });
    });
  }

  closeSearchResults() {
    this.results = [];
    this.isOpen = false;
    this.highlighted = 0;
    this.renderSearchResults();
  }

  prefillFromResult(item) {
    this.query = item.content;
    this.input.value = item.content;
    this.closeSearchResults();
    this.updateSubmitButton();
    // Keep focus on input so user can edit if needed
    this.input.focus();
  }

  async handleSubmit() {
    const content = this.query.trim();
    const language = this.selectedLanguage;

    if (!content || !language) {
      return;
    }

    // Check if already attached
    if (this.selected.find(s => s.content === content && s.language_iso === language)) {
      this.showError('This gloss is already attached.');
      this.showToast('This gloss is already attached.', 'warning');
      return;
    }

    this.submitting = true;
    this.updateSubmitButton();
    this.btnSubmit.innerHTML = '<span class="loading loading-spinner loading-sm"></span>';

    try {
      const formData = new FormData();
      formData.append('content', content);
      formData.append('language', language);

      const response = await fetch(this.createUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': this.getCookie('csrftoken') || '' },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Unable to process');
      }

      if (data.gloss) {
        // Check again in case of race condition
        if (this.selected.find(s => s.id === data.gloss.id)) {
          this.showError('This gloss is already attached.');
          this.showToast('This gloss is already attached.', 'warning');
        } else {
          this.select(data.gloss);

          // Show appropriate toast
          const message = data.created
            ? `Created and attached: ${content}`
            : `Attached existing gloss: ${content}`;
          this.showToast(message, 'success');

          // Clear input but keep language selection
          this.query = '';
          this.input.value = '';
          this.input.focus();
        }
      }
    } catch (err) {
      this.showError(err.message);
      this.showToast(err.message, 'error');
    } finally {
      this.submitting = false;
      this.updateSubmitButton();
      this.btnSubmit.textContent = 'Attach';
    }
  }

  renderSelectedTable() {
    if (this.selected.length === 0) {
      this.selectedTableBody.innerHTML = '<tr><td colspan="3" class="text-center text-light">No items attached.</td></tr>';
      return;
    }

    this.selectedTableBody.innerHTML = this.selected.map(item => `
      <tr>
        <td>${this.escapeHtml(item.content)}</td>
        <td>${this.escapeHtml(item.language_iso)}</td>
        <td class="text-right">
          <div class="flex justify-end gap-2">
            <a href="/glosses/${item.id}/edit/" target="_blank" class="btn btn-ghost btn-xs">Open</a>
            <button type="button" class="btn btn-ghost btn-xs text-error" data-remove-id="${item.id}">Detach</button>
          </div>
        </td>
        <input type="hidden" name="${this.fieldName}" value="${item.id}">
      </tr>
    `).join('');

    // Attach remove button listeners
    this.selectedTableBody.querySelectorAll('[data-remove-id]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = parseInt(btn.getAttribute('data-remove-id'));
        this.remove(id);
      });
    });
  }

  select(item) {
    if (!this.selected.find(s => s.id === item.id)) {
      this.selected.push(item);
      this.renderSelectedTable();
    }
  }

  remove(id) {
    this.selected = this.selected.filter(item => item.id !== id);
    this.renderSelectedTable();
  }

  showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg fixed bottom-4 right-4 w-auto max-w-md z-50 animate-in slide-in-from-bottom`;
    toast.innerHTML = `
      <div>
        <span>${this.escapeHtml(message)}</span>
      </div>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      toast.classList.add('animate-out', 'slide-out-to-bottom');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  showError(message) {
    this.errorDiv.textContent = message;
    this.errorDiv.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
      this.errorDiv.style.display = 'none';
    }, 5000);
  }

  getCookie(name) {
    const cookies = document.cookie ? document.cookie.split('; ') : [];
    for (const cookie of cookies) {
      const [key, ...rest] = cookie.split('=');
      if (key === name) return decodeURIComponent(rest.join('='));
    }
    return null;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
