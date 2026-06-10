const API_BASE = (() => {
  const { hostname, origin, protocol } = window.location;
  if (protocol === "file:") return "http://localhost:8001";
  if (hostname === "localhost" || hostname === "127.0.0.1") return "http://localhost:8001";
  return origin.replace(/\/$/, "");
})();

const state = {
  data: null,
  language: "en",
};

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  // Attach auth token when present (shared session token key used by Elio frontend)
  try {
    // Prefer WisCore-specific token; fallback to Elio token for legacy compatibility
    const wtoken = localStorage.getItem('wiscoreToken');
    const etoken = localStorage.getItem('elioToken');
    const token = wtoken || etoken;
    if (token) headers.set('Authorization', `Bearer ${token}`);
  } catch (e) {}
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${body}`);
  }
  return response.json();
}

function escapeHTML(value) {
  return String(value || "").replace(/[&<>'"]/g, (tag) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[tag]));
}

function formToObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function loadState() {
  state.data = await api("/wiscore/state");
  renderAll();
}

function bindNavigation() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((item) => item.classList.remove("active-view"));
      button.classList.add("active");
      document.getElementById(`view-${button.dataset.view}`).classList.add("active-view");
      const titleMap = {
        public: "Industrial Buying Desk",
        staff: "Sales Command Center",
        sources: "Knowledge Sources",
        bids: "Bid Radar",
      };
      document.getElementById("viewTitle").textContent = titleMap[button.dataset.view];
    });
  });
}

function bindDemoControls() {
  document.getElementById("languageToggle").addEventListener("click", () => {
    state.language = state.language === "en" ? "es" : "en";
    document.getElementById("languageToggle").textContent = state.language === "en" ? "EN / ES" : "ES / EN";
  });

  document.getElementById("resetDemo").addEventListener("click", async () => {
    state.data = await api("/wiscore/reset", { method: "POST" });
    document.getElementById("intakeResult").textContent = "Demo state reset.";
    document.getElementById("assistantTranscript").innerHTML = "";
    renderAll();
  });
}

function bindAssistant() {
  const form = document.getElementById("assistantForm");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = document.getElementById("assistantInput");
      await askAssistant(input.value, true);
    });
  }
}

async function askAssistant(message, includeUserMessage) {
  const transcript = document.getElementById("assistantTranscript");
  if (!transcript) return;
  if (includeUserMessage) {
    transcript.insertAdjacentHTML("beforeend", `<div class="message user">${escapeHTML(message)}</div>`);
  }
  const answer = await api("/wiscore/assistant", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
  const citations = answer.citations.map((citation) => `<div class="citation">${escapeHTML(citation.id)} | ${escapeHTML(citation.title)} | ${escapeHTML(citation.visibility)}</div>`).join("");
  transcript.insertAdjacentHTML(
    "beforeend",
    `<div class="message">
      <strong>Source-backed answer</strong>
      <p>${escapeHTML(answer.answer)}</p>
      <p><strong>Missing info:</strong> ${escapeHTML(answer.missing_info.join(", "))}</p>
      <p><strong>Confidence:</strong> ${escapeHTML(answer.confidence)}</p>
      ${citations}
    </div>`
  );
  transcript.scrollTop = transcript.scrollHeight;
}

function bindIntake() {
  const form = document.getElementById("rfqForm");
  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const result = await api("/wiscore/rfq", {
        method: "POST",
        body: JSON.stringify({ ...formToObject(form), language: state.language }),
      });
      document.getElementById("intakeResult").textContent = `Created ${result.lead.id} and ${result.quote.id}.`;
      await loadState();
    });
  }

  const emergencyBtn = document.getElementById("submitEmergency");
  if (emergencyBtn) {
    emergencyBtn.addEventListener("click", async () => {
      const result = await api("/wiscore/emergency", {
        method: "POST",
        body: JSON.stringify({
          ...formToObject(form),
          language: state.language,
          description: `${form.description.value} Production stopped. Immediate callback requested.`,
        }),
      });
      document.getElementById("intakeResult").textContent = `Emergency routed to ${result.lead.owner}: ${result.lead.id}.`;
      await loadState();
    });
  }
}

function renderAll() {
  if (!state.data) return;
  renderMetrics();
  renderLeads();
  renderSources();
  renderBidsAndFollowups();
}

function renderMetrics() {
  const analytics = state.data.analytics;
  if (!analytics) return;
  const metrics = [
    ["Open leads", analytics.open_leads],
    ["Emergencies", analytics.emergency_count],
    ["Follow-ups", analytics.followups_due],
    ["Quote value", `$${analytics.quote_value.toLocaleString()}`],
    ["Avg bid fit", `${analytics.bid_fit_average}%`],
  ];
  const strip = document.getElementById("metricStrip");
  if (strip) {
    strip.innerHTML = metrics.map(([label, value]) => `<p class="metric"><strong>${escapeHTML(value)}</strong><span>${escapeHTML(label)}</span></p>`).join("");
  }
}

function renderLeads() {
  const rows = document.getElementById("leadRows");
  if (!rows) return;
  rows.innerHTML = state.data.leads.map((lead) => `<tr>
      <td><strong>${escapeHTML(lead.company)}</strong><br><span>${escapeHTML(lead.contact)} | ${escapeHTML(lead.territory)}</span></td>
      <td>${escapeHTML((lead.category || "").replaceAll("_", " "))}</td>
      <td><span class="tag ${escapeHTML(lead.status)}">${escapeHTML(lead.status)}</span></td>
      <td>${escapeHTML(lead.owner || "")}</td>
      <td>${escapeHTML(lead.next_action || "")}<br><small>Missing: ${escapeHTML((lead.missing_info||[]).join(", "))}</small></td>
      <td><button class="row-button" data-draft="${escapeHTML(lead.id)}">Draft</button></td>
    </tr>`).join("");

  document.querySelectorAll("[data-draft]").forEach((button) => {
    button.addEventListener("click", () => draftQuote(button.dataset.draft));
  });
}

async function draftQuote(leadId) {
  const draft = await api(`/wiscore/leads/${encodeURIComponent(leadId)}/quote-draft`);
  const citations = draft.citations.map((citation) => `- ${citation.id}: ${citation.title}`).join("\n");
  const assistant = document.getElementById("quoteAssistant");
  if (assistant) {
    assistant.textContent = `${draft.subject}\n\n${draft.body}\n\nSources used:\n${citations}`;
  }
}

function renderSources() {
  const grid = document.getElementById("sourceGrid");
  if (!grid) return;
  grid.innerHTML = state.data.sources.map((source) => `
    <article class="source-card">
      <code>${escapeHTML(source.id)}</code>
      <h3>${escapeHTML(source.title)}</h3>
      <p>${escapeHTML(source.snippet || "")}</p>
      <div class="source-tags"><span class="tag">${escapeHTML(source.type)}</span>
      <span class="tag">${escapeHTML(source.visibility || "")}</span></div>
      <div class="source-actions"><button class="chunks-toggle" data-id="${escapeHTML(source.id)}">Show chunks</button></div>
      <div class="chunks" id="chunks-${escapeHTML(source.id)}" style="display:none; margin-top:8px;"></div>
    </article>`).join("");

  // Attach chunk toggle handlers
  document.querySelectorAll('.chunks-toggle').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.id;
      const container = document.getElementById(`chunks-${id}`);
      if (!container) return;
      if (container.style.display === 'none') {
        // populate if empty
        if (!container.dataset.populated) {
          const chunks = (state.data.source_chunks || []).filter((c) => c.source_id === id).slice(0,5);
          container.innerHTML = chunks.map((c) => `<div class="chunk"><strong>Chunk ${escapeHTML(c.chunk_id)}</strong><p>${escapeHTML(c.text.substring(0,400))}${c.text.length>400? '…' : ''}</p></div>`).join('');
          if (chunks.length === 0) container.innerHTML = '<div class="chunk">No chunks available.</div>';
          container.dataset.populated = '1';
        }
        container.style.display = 'block';
        btn.textContent = 'Hide chunks';
      } else {
        container.style.display = 'none';
        btn.textContent = 'Show chunks';
      }
    });
  });
}

function renderBidsAndFollowups() {
  const bidList = document.getElementById("bidList");
  if (bidList) {
    bidList.innerHTML = state.data.bid_opportunities.map((bid) => `<article class="bid-card">
        <h3>${escapeHTML(bid.title)}</h3>
        <p>${escapeHTML(bid.agency)} | Due ${escapeHTML(bid.due_date)}</p>
        <p><strong>Fit score:</strong> ${escapeHTML(bid.fit_score)}%</p>
        <p><strong>Checklist:</strong> ${escapeHTML(bid.checklist.join(", "))}</p>
        <p><strong>Lisk flags:</strong> ${escapeHTML(bid.risk_flags.join(", "))}</p>
      </article>`).join("");
  }

  const followupList = document.getElementById("followupList");
  if (followupList) {
    followupList.innerHTML = state.data.followups.map((followup) => `<article class="followup-card">
        <h3>${escapeHTML(followup.company)}</h3>
        <p>${escapeHTML(followup.quote_id)} | ${escapeHTML(followup.age_days)} days quiet | ${escapeHTML(followup.priority)}</p>
        <p>${escapeHTML(followup.draft)}</p>
      </article>`).join("");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  bindAssistant();
  bindIntake();
  bindDemoControls();
  loadState().then(() => askAssistant("What do you need for an air compressor quote?", false));
});