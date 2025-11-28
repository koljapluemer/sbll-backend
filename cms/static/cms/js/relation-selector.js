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
    this.openCreate = false;
    this.newContent = '';
    this.newLanguage = '';
    this.createError = '';
    this.creating = false;

    // Debounce timer
    this.searchDebounce = null;

    // Get DOM elements
    this.selectedTableBody = document.getElementById(`selected-${this.fieldName}`);
    this.searchInput = document.getElementById(`search-${this.fieldName}`);
    this.resultsContainer = document.getElementById(`results-${this.fieldName}`);
    this.modal = document.getElementById(`modal-${this.fieldName}`);
    this.newContentInput = document.getElementById(`new-content-${this.fieldName}`);
    this.newLanguageSelect = document.getElementById(`new-language-${this.fieldName}`);
    this.createErrorDiv = document.getElementById(`create-error-${this.fieldName}`);
    this.btnCreate = document.getElementById(`btn-create-${this.fieldName}`);
    this.btnCancel = document.getElementById(`btn-cancel-${this.fieldName}`);
    this.btnSubmit = document.getElementById(`btn-submit-${this.fieldName}`);
    this.modalBackdrop = document.getElementById(`modal-backdrop-${this.fieldName}`);

    this.init();
  }

  init() {
    // Populate language dropdown
    this.renderLanguageOptions();

    // Initial render
    this.renderSelectedTable();

    // Attach event listeners
    this.searchInput.addEventListener('input', () => this.handleSearchInput());
    this.searchInput.addEventListener('focus', () => this.handleSearchFocus());
    this.searchInput.addEventListener('keydown', (e) => this.handleSearchKeydown(e));
    this.searchInput.addEventListener('blur', () => setTimeout(() => this.handleSearchBlur(), 200));

    this.btnCreate.addEventListener('click', () => this.openCreateModal());
    this.btnCancel.addEventListener('click', () => this.closeCreateModal());
    this.btnSubmit.addEventListener('click', () => this.createAndAttach());
    this.modalBackdrop.addEventListener('click', () => this.closeCreateModal());
  }

  renderLanguageOptions() {
    this.newLanguageSelect.innerHTML = '<option value="">Select language</option>';
    this.languages.forEach(lang => {
      const option = document.createElement('option');
      option.value = lang.id;
      option.textContent = lang.label;
      this.newLanguageSelect.appendChild(option);
    });
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

  handleSearchInput() {
    this.query = this.searchInput.value;

    // Debounce search
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => {
      this.search();
    }, 200);
  }

  handleSearchFocus() {
    if (this.results.length > 0) {
      this.isOpen = true;
      this.renderSearchResults();
    }
  }

  handleSearchBlur() {
    this.isOpen = false;
    this.renderSearchResults();
  }

  handleSearchKeydown(e) {
    if (!this.isOpen) return;

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
      this.attachHighlighted();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      this.resetSearch();
    }
  }

  async search() {
    const term = this.query.trim();
    if (!term) {
      this.results = [];
      this.isOpen = false;
      this.renderSearchResults();
      return;
    }

    this.loading = true;
    this.isOpen = true;
    this.renderSearchResults();

    try {
      const response = await fetch(`${this.searchUrl}?q=${encodeURIComponent(term)}`, {
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
      this.resultsContainer.innerHTML = '<div class="px-3 py-2 text-sm text-light">No matches.</div>';
      return;
    }

    this.resultsContainer.innerHTML = this.results.map((item, idx) => `
      <button
        type="button"
        class="w-full text-left px-3 py-2 hover:bg-base-200 flex justify-between items-center ${idx === this.highlighted ? 'bg-base-200' : ''}"
        data-select-id="${item.id}"
      >
        <span>${this.escapeHtml(item.language_iso)}: ${this.escapeHtml(item.content)}</span>
        <span class="badge badge-ghost">${this.escapeHtml(item.language_iso)}</span>
      </button>
    `).join('');

    // Attach select listeners
    this.resultsContainer.querySelectorAll('[data-select-id]').forEach((btn, idx) => {
      btn.addEventListener('click', () => {
        const id = parseInt(btn.getAttribute('data-select-id'));
        const item = this.results.find(r => r.id === id);
        if (item) this.select(item);
      });
      btn.addEventListener('mouseenter', () => {
        this.highlighted = idx;
        this.renderSearchResults();
      });
    });
  }

  select(item) {
    if (!this.selected.find(s => s.id === item.id)) {
      this.selected.push(item);
      this.renderSelectedTable();
    }
    this.resetSearch();
  }

  remove(id) {
    this.selected = this.selected.filter(item => item.id !== id);
    this.renderSelectedTable();
  }

  attachHighlighted() {
    if (this.results[this.highlighted]) {
      this.select(this.results[this.highlighted]);
    }
  }

  resetSearch() {
    this.query = '';
    this.searchInput.value = '';
    this.results = [];
    this.isOpen = false;
    this.highlighted = 0;
    this.renderSearchResults();
  }

  openCreateModal() {
    this.openCreate = true;
    this.modal.classList.add('modal-open');
  }

  closeCreateModal() {
    this.openCreate = false;
    this.modal.classList.remove('modal-open');
    this.newContent = '';
    this.newLanguage = '';
    this.newContentInput.value = '';
    this.newLanguageSelect.value = '';
    this.createError = '';
    this.createErrorDiv.style.display = 'none';
  }

  async createAndAttach() {
    this.newContent = this.newContentInput.value.trim();
    this.newLanguage = this.newLanguageSelect.value;
    this.createError = '';

    if (!this.newContent || !this.newLanguage) {
      this.createError = 'Content and language are required.';
      this.createErrorDiv.textContent = this.createError;
      this.createErrorDiv.style.display = 'block';
      return;
    }

    this.creating = true;
    this.btnSubmit.disabled = true;
    this.btnSubmit.innerHTML = '<span class="loading loading-spinner loading-sm"></span>';

    try {
      const formData = new FormData();
      formData.append('content', this.newContent);
      formData.append('language', this.newLanguage);

      const response = await fetch(this.createUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-CSRFToken': this.getCookie('csrftoken') || '' },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Unable to create');
      }

      if (data.gloss) {
        this.select(data.gloss);
        this.closeCreateModal();
      }
    } catch (err) {
      this.createError = err.message;
      this.createErrorDiv.textContent = this.createError;
      this.createErrorDiv.style.display = 'block';
    } finally {
      this.creating = false;
      this.btnSubmit.disabled = false;
      this.btnSubmit.textContent = 'Create & attach';
    }
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
