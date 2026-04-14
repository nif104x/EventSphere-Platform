const $ = (id) => document.getElementById(id);
const err = $("err");
const t = { list: $("tList"), ord: $("tOrd"), usr: $("tUsr") };
const p = { list: $("pList"), ord: $("pOrd"), usr: $("pUsr") };
const b = { list: $("bList"), ord: $("bOrd"), usr: $("bUsr") };

function showErr(msg) {
  err.style.display = msg ? "block" : "none";
  err.textContent = msg || "";
}

function tab(name) {
  p.list.style.display = name === "list" ? "block" : "none";
  p.ord.style.display = name === "ord" ? "block" : "none";
  p.usr.style.display = name === "usr" ? "block" : "none";
  t.list.className = name === "list" ? "btn p" : "btn";
  t.ord.className = name === "ord" ? "btn p" : "btn";
  t.usr.className = name === "usr" ? "btn p" : "btn";
}

const m = (v) => Number(v || 0).toFixed(2);

async function load() {
  showErr("");
  try {
    const [L, O, U] = await Promise.all([
      apiGet("/admin/listings"),
      apiGet("/admin/orders"),
      apiGet("/admin/users"),
    ]);
    drawListings(L);
    drawOrders(O);
    drawUsers(U);
  } catch (e) {
    showErr(e.message || "load failed");
  }
}

function drawListings(L) {
  b.list.innerHTML = L.length
    ? ""
    : `<tr><td colspan="5" class="muted">No listings.</td></tr>`;
  for (const x of L) {
    b.list.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${x.id}</td>
        <td>${x.company_name || x.org_id || ""}</td>
        <td>${x.title}</td>
        <td>${m(x.base_price)}</td>
        <td style="text-align:right">
          <button class="btn d" data-del="${x.id}" ${x.is_deleted ? "disabled" : ""}>Del</button>
        </td>
      </tr>`
    );
  }
  b.list.querySelectorAll("button[data-del]").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-del");
      if (btn.disabled) return;
      if (!confirm(`Delete ${id}?`)) return;
      await apiDelete(`/admin/listings/${id}`);
      await load();
    };
  });
}

function drawOrders(O) {
  b.ord.innerHTML = O.length
    ? ""
    : `<tr><td colspan="7" class="muted">No orders.</td></tr>`;
  for (const x of O) {
    b.ord.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${x.order_id}</td>
        <td>${x.customer_name || ""}</td>
        <td>${x.organizer_name || ""}</td>
        <td>${x.event_date || "-"}</td>
        <td>${x.event_status || "-"}</td>
        <td>${x.payment_status || "-"}</td>
        <td>${m(x.total_price_calculated)}</td>
      </tr>`
    );
  }
}

function drawUsers(U) {
  b.usr.innerHTML = U.length
    ? ""
    : `<tr><td colspan="5" class="muted">No users.</td></tr>`;
  for (const x of U) {
    b.usr.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${x.id}</td>
        <td>${x.username}</td>
        <td>${x.role}</td>
        <td>${x.status}</td>
        <td style="text-align:right">
          <button class="btn p" data-u="${x.id}" data-s="${x.status}">${x.status === "Active" ? "Ban" : "Unban"}</button>
        </td>
      </tr>`
    );
  }
  b.usr.querySelectorAll("button[data-u]").forEach((btn) => {
    btn.onclick = async () => {
      const id = btn.getAttribute("data-u");
      const s = btn.getAttribute("data-s");
      const next = s === "Active" ? "Suspended" : "Active";
      await apiPatch(`/admin/users/${id}/status`, { status: next, reason: null });
      await load();
    };
  });
}

$("refresh").onclick = load;
t.list.onclick = () => tab("list");
t.ord.onclick = () => tab("ord");
t.usr.onclick = () => tab("usr");

tab("list");
load();

