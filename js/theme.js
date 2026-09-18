(() => {
  const storageKey = 'core-theme';
  const colorScheme = window.matchMedia('(prefers-color-scheme: dark)');

  const storedTheme = () => {
    try {
      const value = localStorage.getItem(storageKey);
      return value === 'light' || value === 'dark' ? value : null;
    } catch {
      return null;
    }
  };

  const currentTheme = () => (
    document.documentElement.dataset.theme || (colorScheme.matches ? 'dark' : 'light')
  );

  const applyStoredTheme = () => {
    const saved = storedTheme();
    if (saved) document.documentElement.dataset.theme = saved;
  };

  applyStoredTheme();

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('.theme-toggle');
    const label = button?.querySelector('.theme-label');
    if (!button) return;

    const updateButton = () => {
      const active = currentTheme();
      const next = active === 'dark' ? 'light' : 'dark';
      if (label) label.textContent = active === 'dark' ? 'Dark' : 'Light';
      button.setAttribute('aria-label', `Switch to ${next} mode`);
      button.title = `Switch to ${next} mode`;
    };

    button.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem(storageKey, next); } catch { /* Storage can be unavailable. */ }
      updateButton();
    });

    colorScheme.addEventListener('change', () => {
      if (!storedTheme()) updateButton();
    });

    updateButton();
  });
})();
