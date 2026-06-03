document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form[data-enhanced-submit="true"]').forEach(function(form) {
    form.addEventListener('submit', function() {
      const button = form.querySelector('button[type="submit"]');
      if (!button) {
        return;
      }

      const label = button.querySelector('[data-submit-text]');
      const spinner = button.querySelector('[data-submit-spinner]');

      button.disabled = true;

      if (spinner) {
        spinner.style.display = 'inline-block';
      }

      if (label) {
        label.textContent = button.dataset.loadingText || 'Saving...';
      }
    });
  });
});
