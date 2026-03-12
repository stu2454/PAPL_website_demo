/* PAPL reader — sidebar nav + section loading */

let sections = [];
let currentSlug = null;

window.addEventListener('DOMContentLoaded', async () => {
  await loadSections();
  renderSidebar();

  // Check URL for initial section
  const pathSlug = window.location.pathname.replace('/papl/', '').replace('/papl', '');
  if (pathSlug && pathSlug !== '') {
    loadSection(pathSlug);
  }
});

async function loadSections() {
  try {
    const res = await fetch('/api/papl/sections');
    sections = await res.json();
  } catch (e) {
    document.getElementById('sections-nav').innerHTML =
      '<div class="error">Failed to load sections.</div>';
  }
}

function renderSidebar() {
  const nav = document.getElementById('sections-nav');
  nav.innerHTML = sections.map(s => `
    <button class="papl-nav-item ${currentSlug === s.slug ? 'active' : ''}"
            data-slug="${s.slug}"
            onclick="loadSection('${s.slug}')">
      ${s.title}
    </button>
  `).join('');
}

async function loadSection(slug) {
  currentSlug = slug;
  renderSidebar();

  history.pushState(null, '', `/papl/${slug}`);

  document.getElementById('papl-body').innerHTML = '<div class="loading">Loading…</div>';

  try {
    const res = await fetch(`/api/papl/${slug}`);
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();

    const header = document.getElementById('section-header');
    header.style.display = 'flex';
    document.getElementById('breadcrumb-title').textContent = data.title;
    document.getElementById('api-link').href = `/api/papl/${slug}`;

    const body = document.getElementById('papl-body');
    body.className = 'papl-body';
    body.innerHTML = data.content_html;

    document.title = `${data.title} — NDIS Pricing`;
    renderToc(data.headings);
    window.scrollTo({ top: 0, behavior: 'smooth' });

  } catch (e) {
    document.getElementById('papl-body').innerHTML =
      `<div class="error">Failed to load section "${slug}".</div>`;
  }
}

function renderToc(headings) {
  const toc = document.getElementById('papl-toc');
  const nav = document.getElementById('toc-nav');

  const filtered = headings.filter(h => h.level >= 2 && h.level <= 4);
  if (filtered.length < 2) { toc.style.display = 'none'; return; }

  toc.style.display = 'block';
  nav.innerHTML = filtered.map(h => {
    const cls = h.level === 2 ? '' : h.level === 3 ? 'toc-h3' : 'toc-h4';
    return `<a class="toc-link ${cls}" href="#${h.anchor}">${h.text}</a>`;
  }).join('');
}

window.loadSection = loadSection;
