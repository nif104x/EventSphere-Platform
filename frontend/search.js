const elQ = document.getElementById("q");
const elCat = document.getElementById("cat");
const elMin = document.getElementById("min");
const elMax = document.getElementById("max");
const elBtn = document.getElementById("searchBtn");
const elResults = document.getElementById("results");
const elError = document.getElementById("errorBox");
const elApiText = document.getElementById("apiText");

function showError(msg) {
  if (!msg) {
    elError.style.display = "none";
    elError.textContent = "";
    return;
  }
  elError.style.display = "block";
  elError.textContent = msg;
}

function money(v) {
  const n = Number(v || 0);
  return n.toFixed(2);
}

function currentQueryString() {
  return qs({
    query: elQ.value,
    category: elCat.value,
    min_price: elMin.value,
    max_price: elMax.value,
  });
}

async function runSearch() {
  showError("");
  elResults.innerHTML = "";

  const qstr = currentQueryString();
  elApiText.textContent = `${API_BASE}/search${qstr}`;

  try {
    const results = await apiGet(`/search${qstr}`);
    renderResults(results);
  } catch (e) {
    showError(e.message || "Search failed");
  }
}

function renderResults(results) {
  elResults.innerHTML = "";

  if (!results.length) {
    elResults.innerHTML = `<div class="card"><div class="muted">No results.</div></div>`;
    return;
  }

  for (const r of results) {
    const addons = (r.addons || [])
      .map((a) => `<li>${a.addon_name} (${money(a.price)})</li>`)
      .join("");

    const addonsBlock = r.addons && r.addons.length
      ? `<ul style="margin:6px 0 0 0; padding-left:16px">${addons}</ul>`
      : `<div class="muted" style="margin-top:6px">No addons.</div>`;

    elResults.insertAdjacentHTML(
      "beforeend",
      `<div class="card">
        <div class="row">
          <div>
            <div style="font-size:18px; font-weight:700">${r.title}</div>
            <div class="muted">${r.company_name || r.org_id} • ${r.category}</div>
          </div>
          <div class="spacer"></div>
          <div style="text-align:right">
            <div class="muted">Base</div>
            <div style="font-size:18px; font-weight:800">${money(r.base_price)}</div>
          </div>
        </div>

        ${r.image_url ? `<div class="muted" style="margin-top:10px">Image: <span class="mono">${r.image_url}</span></div>` : ""}

        <div style="margin-top:10px; font-weight:700">Addons</div>
        ${addonsBlock}
      </div>`
    );
  }
}

elBtn.addEventListener("click", runSearch);
elQ.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
elCat.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
elMin.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
elMax.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });

runSearch();

