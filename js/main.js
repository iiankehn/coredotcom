(() => {
  const button = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.mobile-nav');

  if (!button || !menu) return;

  const closeMenu = (returnFocus = false) => {
    button.setAttribute('aria-expanded', 'false');
    menu.hidden = true;
    if (returnFocus) button.focus();
  };

  const openMenu = () => {
    button.setAttribute('aria-expanded', 'true');
    menu.hidden = false;
    menu.querySelector('a')?.focus();
  };

  button.addEventListener('click', () => {
    const isOpen = button.getAttribute('aria-expanded') === 'true';
    isOpen ? closeMenu() : openMenu();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !menu.hidden) closeMenu(true);
  });

  document.addEventListener('click', (event) => {
    if (!menu.hidden && !menu.contains(event.target) && !button.contains(event.target)) {
      closeMenu();
    }
  });

  menu.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });

  const desktop = window.matchMedia('(min-width: 48.01rem)');
  desktop.addEventListener('change', (event) => {
    if (event.matches) closeMenu();
  });
})();
