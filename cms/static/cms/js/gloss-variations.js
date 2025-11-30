document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('variations-modal');
  const variationsContent = document.getElementById('variations-content');

  document.querySelectorAll('.generate-variations').forEach(function(link) {
    link.addEventListener('click', async function(e) {
      e.preventDefault();

      const glossId = this.dataset.glossId;
      const numVariations = parseInt(this.dataset.num);

      variationsContent.innerHTML = '<div class="text-center"><span class="loading loading-spinner"></span> Generating variations...</div>';
      modal.showModal();

      try {
        const response = await fetch('/api/ai/gloss-variations/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({
            gloss_id: glossId,
            num_variations: numVariations
          })
        });

        if (!response.ok) {
          throw new Error('Failed to generate variations');
        }

        const data = await response.json();

        let html = '<ul class="list-disc list-inside space-y-2">';
        data.variations.forEach(function(variation) {
          html += '<li>' + escapeHtml(variation) + '</li>';
        });
        html += '</ul>';

        variationsContent.innerHTML = html;
      } catch (error) {
        variationsContent.innerHTML = '<div class="text-error">Error: ' + escapeHtml(error.message) + '</div>';
      }
    });
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});
