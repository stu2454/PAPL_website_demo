/* Catalogue page — search, filter, paginate */

const CG_CATEGORIES = [3, 5, 6]; // categories covered by the AT Code Guide

const PAGE_SIZE = 50;
let state = {
  q: '',
  category: '',
  registration_group: '',
  type: '',
  include_legacy: false,
  offset: 0,
};

// --- Init ---

window.addEventListener('DOMContentLoaded', async () => {
  // Read query params
  const params = new URLSearchParams(window.location.search);
  if (params.get('q')) { state.q = params.get('q'); document.getElementById('search-input').value = state.q; }
  if (params.get('category')) state.category = params.get('category');
  if (params.get('type')) { state.type = params.get('type'); }

  await populateCategories();
  await populateRegGroups();
  applyStateToForm();
  fetchAndRender();

  // Toggle persistence
  initToggle(() => fetchAndRender());

  // Event listeners
  let searchTimer;
  document.getElementById('search-input').addEventListener('input', (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.q = e.target.value.trim();
      state.offset = 0;
      fetchAndRender();
    }, 300);
  });

  document.getElementById('category-select').addEventListener('change', (e) => {
    state.category = e.target.value;
    state.offset = 0;
    populateRegGroups();
    fetchAndRender();
  });

  document.getElementById('reg-group-select').addEventListener('change', (e) => {
    state.registration_group = e.target.value;
    state.offset = 0;
    fetchAndRender();
  });

  document.getElementById('type-select').addEventListener('change', (e) => {
    state.type = e.target.value;
    state.offset = 0;
    fetchAndRender();
  });

  document.getElementById('legacy-check').addEventListener('change', (e) => {
    state.include_legacy = e.target.checked;
    state.offset = 0;
    fetchAndRender();
  });

  document.getElementById('reset-btn').addEventListener('click', () => {
    state = { q: '', category: '', registration_group: '', type: '', include_legacy: false, offset: 0 };
    applyStateToForm();
    fetchAndRender();
  });
});

function applyStateToForm() {
  document.getElementById('search-input').value = state.q;
  document.getElementById('category-select').value = state.category;
  document.getElementById('type-select').value = state.type;
  document.getElementById('legacy-check').checked = state.include_legacy;
}

// --- Data fetching ---

function buildApiUrl() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (state.category) p.set('category', state.category);
  if (state.registration_group) p.set('registration_group', state.registration_group);
  if (state.type) p.set('type', state.type);
  if (state.include_legacy) p.set('include_legacy', 'true');
  p.set('limit', PAGE_SIZE);
  p.set('offset', state.offset);
  return `/api/support-items?${p}`;
}

async function fetchAndRender() {
  document.getElementById('items-container').innerHTML = '<div class="loading">Loading…</div>';
  try {
    const res = await fetch(buildApiUrl());
    const data = await res.json();
    renderTable(data);
    renderPagination(data.total);
  } catch (e) {
    document.getElementById('items-container').innerHTML = '<div class="error">Failed to load data.</div>';
  }
}

async function populateCategories() {
  const res = await fetch('/api/categories');
  const cats = await res.json();
  const sel = document.getElementById('category-select');
  cats.forEach(cat => {
    const opt = document.createElement('option');
    opt.value = cat.number;
    opt.textContent = `${cat.number}. ${cat.name} (${cat.item_count})`;
    sel.appendChild(opt);
  });
}

async function populateRegGroups() {
  const p = new URLSearchParams();
  if (state.category) p.set('category', state.category);
  const res = await fetch(`/api/registration-groups?${p}`);
  const groups = await res.json();
  const sel = document.getElementById('reg-group-select');
  // Keep current value if still valid
  const current = state.registration_group;
  sel.innerHTML = '<option value="">All groups</option>';
  groups.forEach(rg => {
    const opt = document.createElement('option');
    opt.value = rg.number;
    opt.textContent = `${rg.number} — ${rg.name} (${rg.item_count})`;
    sel.appendChild(opt);
  });
  if (current && groups.find(g => g.number === current)) {
    sel.value = current;
  } else {
    state.registration_group = '';
  }
}

// --- Rendering ---

function cgBadge(item) {
  if (!cgEnabled() || !CG_CATEGORIES.includes(item.support_category_number)) return '';
  return '<span class="cat-cg-badge" title="AT &amp; HM Code Guide applies">Code Guide</span>';
}

function typePillHtml(item) {
  if (item.legacy) return '<span class="type-pill type-pill--legacy">Legacy</span>';
  const t = item.type || '';
  if (t === 'Price Limited Supports') return '<span class="type-pill type-pill--limited">Price limited</span>';
  if (t === 'Quotable Supports')      return '<span class="type-pill type-pill--quote">Quotable</span>';
  if (t === 'Unit Price = $1')         return '<span class="type-pill type-pill--unit">Unit = $1</span>';
  return '';
}

function renderTable(data) {
  const count = document.getElementById('result-count');
  count.textContent = `${data.total.toLocaleString()} item${data.total !== 1 ? 's' : ''}`;

  if (data.items.length === 0) {
    document.getElementById('items-container').innerHTML =
      '<div class="loading">No items match your filters.</div>';
    return;
  }

  const rows = data.items.map(item => {
    const price = item.national_price != null
      ? `$${item.national_price.toFixed(2)}`
      : (item.requires_quote ? 'By quote' : '—');

    return `<tr onclick="window.location='/catalogue/${encodeURIComponent(item.support_item_number)}'">
      <td><span class="item-num">${item.support_item_number}</span></td>
      <td>${item.name}${cgBadge(item)}</td>
      <td>${item.support_category_number}. ${item.support_category_name}</td>
      <td>${item.unit_label}</td>
      <td class="price-cell">${price}</td>
      <td>${typePillHtml(item)}</td>
    </tr>`;
  }).join('');

  document.getElementById('items-container').innerHTML = `
    <table class="items-table">
      <thead>
        <tr>
          <th>Item number</th>
          <th>Name</th>
          <th>Category</th>
          <th>Unit</th>
          <th style="text-align:right">NSW price</th>
          <th>Type</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderPagination(total) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(state.offset / PAGE_SIZE);
  const el = document.getElementById('pagination');

  if (totalPages <= 1) { el.innerHTML = ''; return; }

  const pages = [];
  pages.push(`<button class="page-btn" ${currentPage === 0 ? 'disabled' : ''} onclick="goPage(${currentPage - 1})">← Prev</button>`);

  for (let i = 0; i < totalPages; i++) {
    if (i === 0 || i === totalPages - 1 || Math.abs(i - currentPage) <= 2) {
      pages.push(`<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goPage(${i})">${i + 1}</button>`);
    } else if (Math.abs(i - currentPage) === 3) {
      pages.push(`<span style="padding:0 0.25rem;color:var(--color-text-muted)">…</span>`);
    }
  }

  pages.push(`<button class="page-btn" ${currentPage === totalPages - 1 ? 'disabled' : ''} onclick="goPage(${currentPage + 1})">Next →</button>`);
  el.innerHTML = pages.join('');
}

function goPage(page) {
  state.offset = page * PAGE_SIZE;
  fetchAndRender();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
