const els = {
  refreshBtn: document.getElementById("refreshBtn"),
  errorBox: document.getElementById("errorBox"),

  tabListings: document.getElementById("tabListings"),
  tabOrders: document.getElementById("tabOrders"),
  tabUsers: document.getElementById("tabUsers"),

  panelListings: document.getElementById("panelListings"),
  panelOrders: document.getElementById("panelOrders"),
  panelUsers: document.getElementById("panelUsers"),

  listingsBody: document.getElementById("listingsBody"),
  ordersBody: document.getElementById("ordersBody"),
  usersBody: document.getElementById("usersBody"),
};

function showError(msg) {
  if (!msg) {
    els.errorBox.style.display = "none";
    els.errorBox.textContent = "";
    return;
  }
  els.errorBox.style.display = "block";
  els.errorBox.textContent = msg;
}

function setTab(tab) {
  const isListings = tab === "listings";
  const isOrders = tab === "orders";
  const isUsers = tab === "users";

  els.panelListings.style.display = isListings ? "block" : "none";
  els.panelOrders.style.display = isOrders ? "block" : "none";
  els.panelUsers.style.display = isUsers ? "block" : "none";

  els.tabListings.className = isListings ? "btn btn-primary" : "btn";
  els.tabOrders.className = isOrders ? "btn btn-primary" : "btn";
  els.tabUsers.className = isUsers ? "btn btn-primary" : "btn";
}

function money(v) {
  const n = Number(v || 0);
  return n.toFixed(2);
}

async function loadAll() {
  showError("");
  try {
    const [listings, orders, users] = await Promise.all([
      apiGet("/admin/listings"),
      apiGet("/admin/orders"),
      apiGet("/admin/users"),
    ]);
    renderListings(listings);
    renderOrders(orders);
    renderUsers(users);
  } catch (e) {
    showError(e.message || "Failed to load admin data");
  }
}

function renderListings(listings) {
  els.listingsBody.innerHTML = "";

  if (!listings.length) {
    els.listingsBody.innerHTML = `<tr><td colspan="7" class="muted">No listings found.</td></tr>`;
    return;
  }

  for (const l of listings) {
    const status = l.is_deleted
      ? `<span class="badge badge-bad">deleted</span>`
      : `<span class="badge badge-ok">active</span>`;

    const btn = l.is_deleted
      ? `<button class="btn btn-danger" disabled style="opacity:.4; cursor:not-allowed">Delete</button>`
      : `<button class="btn btn-danger" data-del="${l.id}">Delete</button>`;

    els.listingsBody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${l.id}</td>
        <td>${l.company_name || l.org_id || ""}</td>
        <td>${l.category}</td>
        <td>${l.title}</td>
        <td>${money(l.base_price)}</td>
        <td>${status}</td>
        <td style="text-align:right">${btn}</td>
      </tr>`
    );
  }

  els.listingsBody.querySelectorAll("button[data-del]").forEach((b) => {
    b.addEventListener("click", async () => {
      const id = b.getAttribute("data-del");
      if (!confirm(`Delete listing ${id}?`)) return;
      try {
        await apiDelete(`/admin/listings/${id}`);
        await loadAll();
      } catch (e) {
        alert(e.message || "Delete failed");
      }
    });
  });
}

function renderOrders(orders) {
  els.ordersBody.innerHTML = "";

  if (!orders.length) {
    els.ordersBody.innerHTML = `<tr><td colspan="9" class="muted">No orders found.</td></tr>`;
    return;
  }

  for (const o of orders) {
    const addonsHtml = (o.addons || [])
      .map((a) => `<li>${a.addon_name || a.addon_id} (${money(a.unit_price)})</li>`)
      .join("");

    const addonsBlock = o.addons && o.addons.length
      ? `<ul style="margin:0; padding-left:16px">${addonsHtml}</ul>`
      : `<span class="muted">None</span>`;

    els.ordersBody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${o.order_id}</td>
        <td>${o.customer_name || ""}<div class="muted">${o.customer_id || ""}</div></td>
        <td>${o.organizer_name || ""}<div class="muted">${o.org_id || ""}</div></td>
        <td>${o.event_date || "-"}</td>
        <td>${o.event_status || "-"}</td>
        <td>${o.payment_status || "-"}</td>
        <td>${money(o.base_price_at_booking)}</td>
        <td>
          ${addonsBlock}
          <div style="margin-top:6px; font-weight:600">Addons total: ${money(o.addons_total)}</div>
        </td>
        <td style="font-weight:700">${money(o.total_price_calculated)}</td>
      </tr>`
    );
  }
}

function renderUsers(users) {
  els.usersBody.innerHTML = "";

  if (!users.length) {
    els.usersBody.innerHTML = `<tr><td colspan="5" class="muted">No users found.</td></tr>`;
    return;
  }

  for (const u of users) {
    const statusBadge =
      u.status === "Active"
        ? `<span class="badge badge-ok">Active</span>`
        : `<span class="badge badge-bad">${u.status}</span>`;

    const actionText = u.status === "Active" ? "Ban" : "Unban";

    els.usersBody.insertAdjacentHTML(
      "beforeend",
      `<tr>
        <td class="mono">${u.id}</td>
        <td>${u.username}</td>
        <td>${u.role}</td>
        <td>${statusBadge}</td>
        <td style="text-align:right">
          <button class="btn btn-primary" data-user="${u.id}" data-status="${u.status}">${actionText}</button>
        </td>
      </tr>`
    );
  }

  els.usersBody.querySelectorAll("button[data-user]").forEach((b) => {
    b.addEventListener("click", async () => {
      const id = b.getAttribute("data-user");
      const status = b.getAttribute("data-status");
      const next = status === "Active" ? "Suspended" : "Active";
      try {
        await apiPatch(`/admin/users/${id}/status`, {
          status: next,
          reason: next === "Suspended" ? "Suspended by admin" : null,
        });
        await loadAll();
      } catch (e) {
        alert(e.message || "Update failed");
      }
    });
  });
}

els.refreshBtn.addEventListener("click", loadAll);
els.tabListings.addEventListener("click", () => setTab("listings"));
els.tabOrders.addEventListener("click", () => setTab("orders"));
els.tabUsers.addEventListener("click", () => setTab("users"));

setTab("listings");
loadAll();

