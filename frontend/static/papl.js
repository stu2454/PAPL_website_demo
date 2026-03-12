/* PAPL reader — sidebar nav + section loading + Code Guide integration */

let sections = [];
let atcgSections = [];
let currentSlug = null;
let currentSource = 'papl'; // 'papl' or 'atcg'

window.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([loadSections(), loadAtcgSections()]);
  renderSidebar();

  initToggle((enabled) => {
    renderSidebar();
    // If currently viewing an ATCG section and toggle is turned off, clear it
    if (!enabled && currentSource === 'atcg') {
      document.getElementById('papl-body').innerHTML = '<div class="papl-welcome"><p>Select a section from the sidebar.</p></div>';
      document.getElementById('section-header').style.display = 'none';
      document.getElementById('papl-toc').style.display = 'none';
      currentSource = 'papl';
    }
  });

  // Check URL for initial section
  const pathSlug = window.location.pathname.replace('/papl/', '').replace('/papl', '');
  if (pathSlug && pathSlug !== '') {
    loadSection(pathSlug, 'papl');
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

async function loadAtcgSections() {
  try {
    const res = await fetch('/api/atcg/sections');
    atcgSections = await res.json();
  } catch (e) {
    atcgSections = [];
  }
}

function renderSidebar() {
  const nav = document.getElementById('sections-nav');
  const cgOn = cgEnabled();

  let html = sections.map(s => `
    <button class="papl-nav-item ${currentSlug === s.slug && currentSource === 'papl' ? 'active' : ''}"
            data-slug="${s.slug}" data-source="papl"
            onclick="loadSection('${s.slug}', 'papl')">
      ${s.title}
    </button>
  `).join('');

  if (cgOn && atcgSections.length) {
    html += `<div class="papl-nav-divider">AT &amp; HM Code Guide</div>`;
    html += atcgSections
      .filter(s => s.relevant_categories.length > 0)
      .map(s => `
        <button class="papl-nav-item papl-nav-item--cg ${currentSlug === s.slug && currentSource === 'atcg' ? 'active' : ''}"
                data-slug="${s.slug}" data-source="atcg"
                onclick="loadSection('${s.slug}', 'atcg')">
          ${s.title}
          <small style="display:block;font-size:0.7rem;opacity:0.7;font-weight:400">
            Cat ${s.relevant_categories.join(', ')}
          </small>
        </button>
      `).join('');
  }

  nav.innerHTML = html;
}

async function loadSection(slug, source) {
  source = source || 'papl';
  currentSlug = slug;
  currentSource = source;

  renderSidebar(); // update active states

  history.pushState(null, '', source === 'papl' ? `/papl/${slug}` : `/papl`);

  document.getElementById('papl-body').innerHTML = '<div class="loading">Loading…</div>';

  try {
    const endpoint = source === 'atcg' ? `/api/atcg/${slug}` : `/api/papl/${slug}`;
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();

    // Update breadcrumb
    const header = document.getElementById('section-header');
    header.style.display = 'flex';
    document.getElementById('breadcrumb-title').textContent =
      source === 'atcg' ? `Code Guide › ${data.title}` : data.title;
    document.getElementById('api-link').href = endpoint;

    // Render content
    const body = document.getElementById('papl-body');
    body.className = 'papl-body';

    // If Code Guide section, wrap with panel styling
    if (source === 'atcg') {
      body.innerHTML = `
        <div class="cg-panel" style="margin-bottom:1.5rem">
          <div class="cg-panel-header">
            <span class="cg-panel-badge">+ Code Guide</span>
            <span class="cg-panel-title">AT &amp; HM Code Guide</span>
          </div>
        </div>
        ${data.content_html}
      `;
    } else {
      body.innerHTML = data.content_html;
    }

    document.title = `${data.title} — NDIS Pricing`;
    renderToc(data.headings, source);
    window.scrollTo({ top: 0, behavior: 'smooth' });

  } catch (e) {
    document.getElementById('papl-body').innerHTML =
      `<div class="error">Failed to load section "${slug}".</div>`;
  }
}

function renderToc(headings, source) {
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
