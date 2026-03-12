/* Code Guide toggle — shared across all pages */

const CG_KEY = 'ndis-cg-enabled';

function cgEnabled() {
  return localStorage.getItem(CG_KEY) === 'true';
}

function initToggle(onChange) {
  const input = document.getElementById('cg-toggle-input');
  if (!input) return;

  input.checked = cgEnabled();

  input.addEventListener('change', () => {
    localStorage.setItem(CG_KEY, input.checked);
    if (onChange) onChange(input.checked);
  });
}
