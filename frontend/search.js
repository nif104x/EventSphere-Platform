const $ = (id) => document.getElementById(id);
const err = $("err");
const out = $("out");
const m = (v) => Number(v || 0).toFixed(2);

function showErr(msg) {
  err.style.display = msg ? "block" : "none";
  err.textContent = msg || "";
}

function qstr() {
  return qs({
    query: $("q").value,
    category: $("cat").value,
    min_price: $("min").value,
    max_price: $("max").value,
  });
}

async function go() {
  showErr("");
  out.innerHTML = "";
  try {
    const r = await apiGet(`/search${qstr()}`);
    if (!r.length) {
      out.innerHTML = `<div class="muted">No results.</div>`;
      return;
    }
    out.innerHTML = r
      .map(
        (x) =>
          `<div style="border-top:1px solid #ddd; padding:8px 0">
            <b>${x.title}</b> <span class="muted">(${x.category})</span><br/>
            <span class="muted">${x.company_name || x.org_id}</span><br/>
            <span>Base: ${m(x.base_price)}</span>
          </div>`
      )
      .join("");
  } catch (e) {
    showErr(e.message || "search failed");
  }
}

$("go").onclick = go;
["q", "cat", "min", "max"].forEach((id) => {
  $(id).addEventListener("keydown", (e) => e.key === "Enter" && go());
});
go();

