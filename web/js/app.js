/* ==========================================================================
   SNEAKER PULSE COMMAND CENTER - MAIN CONTROLLER & MARKET SCANNER
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const bootOverlay = document.getElementById("boot-overlay");
  const bootFill = document.getElementById("boot-fill");
  const lastUpdateTime = document.getElementById("last-update-time");
  const sneakersContainer = document.getElementById("sneakers-container");
  const systemLogContainer = document.getElementById("system-terminal-log");

  // Search Elements
  const searchInput = document.getElementById("market-search-input");
  const searchClearBtn = document.getElementById("search-clear-btn");
  const searchStatusBar = document.getElementById("search-status-bar");
  const searchStatusText = document.getElementById("search-status-text");
  const searchResultsContainer = document.getElementById("search-results-container");

  // Metric Elements
  const statTotalModels = document.getElementById("stat-total-models");
  const statTargetHits = document.getElementById("stat-target-hits");
  const statAlltimeLows = document.getElementById("stat-alltime-lows");
  const statAvgDiscount = document.getElementById("stat-avg-discount");

  // Buttons
  const btnCollect = document.getElementById("btn-collect");
  const btnSeed = document.getElementById("btn-seed");
  const btnRefresh = document.getElementById("btn-refresh");

  let searchDebounceTimer = null;
  let currentlyPinnedIds = new Set();

  // Initial Boot Sequence
  runBootSequence();

  function runBootSequence() {
    let progress = 0;
    const interval = setInterval(() => {
      progress += 25;
      if (bootFill) bootFill.style.width = progress + "%";

      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          if (bootOverlay) bootOverlay.classList.add("hidden");
          loadDashboardData();
        }, 400);
      }
    }, 200);
  }

  function logTerminal(message, isAlert = false) {
    if (!systemLogContainer) return;
    const now = new Date().toLocaleTimeString();
    const entry = document.createElement("div");
    entry.className = `terminal-entry ${isAlert ? "alert" : ""}`;
    entry.innerHTML = `<span class="timestamp">[${now}]</span> ${message}`;
    systemLogContainer.prepend(entry);
  }

  async function loadDashboardData() {
    try {
      updateTimestamp();
      logTerminal("Sincronizando dados dos tênis fixados no SQLite...");

      const [summaryRes, historyRes, pinnedRes] = await Promise.all([
        fetch("/api/summary"),
        fetch("/api/history"),
        fetch("/api/sneakers/pinned")
      ]);

      const summaryData = await summaryRes.json();
      const historyData = await historyRes.json();
      const pinnedData = await pinnedRes.json();

      currentlyPinnedIds = new Set(pinnedData.map(p => p.id));

      renderMetrics(summaryData.summaries, summaryData.alerts);
      renderSneakersGrid(summaryData.summaries);

      if (typeof SneakerCharts !== "undefined") {
        SneakerCharts.renderPriceHistory(historyData);
        SneakerCharts.renderSourceComparison(summaryData.summaries);
      }

      if (summaryData.alerts && summaryData.alerts.length > 0) {
        summaryData.alerts.forEach(a => logTerminal(`🔔 ${a.message}`, true));
      } else {
        logTerminal("Varredura de telemetria concluída. Radar ativo.");
      }

    } catch (err) {
      logTerminal(`❌ Erro de conexão com o servidor API: ${err.message}`, true);
    }
  }

  function updateTimestamp() {
    if (lastUpdateTime) {
      lastUpdateTime.textContent = new Date().toLocaleTimeString();
    }
  }

  function animateCount(element, target, prefix = "", suffix = "") {
    if (!element) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 20));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      element.textContent = `${prefix}${current}${suffix}`;
    }, 30);
  }

  function renderMetrics(summaries, alerts) {
    if (!summaries) return;

    const totalModels = summaries.length;
    const targetHits = summaries.filter(s => s.target_hit).length;
    const alltimeLows = summaries.filter(s => s.all_time_low_hit).length;

    const avgDiscount = (
      summaries.reduce((acc, s) => acc + s.discount_from_max_pct, 0) / (totalModels || 1)
    ).toFixed(1);

    animateCount(statTotalModels, totalModels);
    animateCount(statTargetHits, targetHits);
    animateCount(statAlltimeLows, alltimeLows);
    if (statAvgDiscount) statAvgDiscount.textContent = `${avgDiscount}%`;
  }

  function renderSneakersGrid(summaries) {
    if (!sneakersContainer) return;
    sneakersContainer.innerHTML = "";

    if (!summaries || summaries.length === 0) {
      sneakersContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">
          Nenhum tênis fixado no momento. Use o <strong>Market Scanner</strong> acima para buscar e fixar modelos!
        </div>
      `;
      return;
    }

    summaries.forEach(s => {
      const card = document.createElement("div");
      card.className = "sneaker-card";

      const isTargetHit = s.target_hit;
      const badgeClass = isTargetHit ? "hit" : "watching";
      const badgeText = isTargetHit ? "TARGET HIT 🎯" : "MONITORANDO";

      card.innerHTML = `
        <div class="card-badge-row">
          <span class="badge-target ${badgeClass}">${badgeText}</span>
          <button class="btn-unpin" data-id="${s.sneaker_id}" title="Desafixar do radar">🗑️ Desafixar</button>
        </div>

        <div class="sneaker-title">${s.name}</div>
        <div class="sneaker-colorway">${s.colorway} (${s.size})</div>

        <div class="card-metrics">
          <div class="metric-item">
            <div class="label">Melhor Preço Atual</div>
            <div class="value best">R$ ${s.current_best_price.toFixed(2)}</div>
          </div>
          <div class="metric-item">
            <div class="label">Preço Alvo</div>
            <div class="value">R$ ${s.target_price.toFixed(2)}</div>
          </div>
          <div class="metric-item">
            <div class="label">Menor Histórico</div>
            <div class="value drop">R$ ${s.all_time_lowest_price.toFixed(2)}</div>
          </div>
          <div class="metric-item">
            <div class="label">Queda em Pico</div>
            <div class="value drop">-${s.discount_from_max_pct}%</div>
          </div>
        </div>

        <div class="card-footer-info">
          <span>Menor em ${s.all_time_lowest_date}</span>
          <span class="source-tag">${s.current_best_source}</span>
        </div>
      `;

      // Event Listener para Desafixar
      const unpinBtn = card.querySelector(".btn-unpin");
      if (unpinBtn) {
        unpinBtn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const idToUnpin = unpinBtn.getAttribute("data-id");
          logTerminal(`Desafixando tênis ID '${idToUnpin}' do radar...`);
          await fetch(`/api/sneakers/pin/${idToUnpin}`, { method: "DELETE" });
          currentlyPinnedIds.delete(idToUnpin);
          await loadDashboardData();
        });
      }

      sneakersContainer.appendChild(card);
      if (typeof initCardTilt === "function") {
        initCardTilt(card);
      }
    });
  }

  // Market Scanner Search Functions
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value;
      if (searchClearBtn) {
        searchClearBtn.classList.toggle("hidden", query.length === 0);
      }

      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        performMarketSearch(query);
      }, 300);
    });
  }

  if (searchClearBtn) {
    searchClearBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      searchClearBtn.classList.add("hidden");
      if (searchResultsContainer) searchResultsContainer.classList.add("hidden");
      if (searchStatusBar) searchStatusBar.classList.add("hidden");
    });
  }

  // Keyboard Shortcuts ('/' to search, 'ESC' to clear)
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== searchInput) {
      e.preventDefault();
      if (searchInput) searchInput.focus();
    } else if (e.key === "Escape" && document.activeElement === searchInput) {
      if (searchClearBtn) searchClearBtn.click();
    }
  });

  async function performMarketSearch(query) {
    if (!query || query.trim().length === 0) {
      if (searchResultsContainer) searchResultsContainer.classList.add("hidden");
      if (searchStatusBar) searchStatusBar.classList.add("hidden");
      return;
    }

    if (searchStatusBar) searchStatusBar.classList.remove("hidden");
    if (searchStatusText) searchStatusText.textContent = "SCANNING MARKETPLACES & TELEMETRY...";

    // Dispara animação do Laser 3D Three.js
    if (typeof window.triggerLaserScan === "function") {
      window.triggerLaserScan();
    }

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const results = await res.json();

      renderSearchResults(results);
      logTerminal(`Busca por '${query}' finalizada. ${results.length} resultados encontrados.`);

    } catch (err) {
      logTerminal(`Erro ao buscar modelos: ${err.message}`, true);
    } finally {
      if (searchStatusText) searchStatusText.textContent = "VARREDURA CONCLUÍDA";
    }
  }

  function renderSearchResults(results) {
    if (!searchResultsContainer) return;
    searchResultsContainer.innerHTML = "";
    searchResultsContainer.classList.remove("hidden");

    if (!results || results.length === 0) {
      searchResultsContainer.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 1.5rem;">
          Nenhum modelo encontrado para este termo de busca.
        </div>
      `;
      return;
    }

    results.forEach(sneaker => {
      const isPinned = currentlyPinnedIds.has(sneaker.id);

      const card = document.createElement("div");
      card.className = "search-result-card";
      card.innerHTML = `
        <div class="product-img-wrapper">
          <img src="${sneaker.image_url}" alt="${sneaker.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600'">
        </div>
        <div class="search-title">${sneaker.name}</div>
        <div class="search-colorway">${sneaker.colorway} (${sneaker.size})</div>

        <div class="search-price-row">
          <div>
            <div style="font-size: 0.65rem; color: var(--text-muted);">PREÇO ESTIMADO</div>
            <div class="search-price">R$ ${sneaker.estimated_price ? sneaker.estimated_price.toFixed(2) : sneaker.target_price.toFixed(2)}</div>
          </div>
          <button class="btn-pin-target ${isPinned ? 'pinned' : ''}" data-sneaker='${JSON.stringify(sneaker).replace(/'/g, "&apos;")}'>
            ${isPinned ? '📌 FIXADO' : '🎯 FIXAR ALVO'}
          </button>
        </div>
      `;

      const pinBtn = card.querySelector(".btn-pin-target");
      if (pinBtn && !isPinned) {
        pinBtn.addEventListener("click", async () => {
          const sneakerData = JSON.parse(pinBtn.getAttribute("data-sneaker").replace(/&apos;/g, "'"));
          logTerminal(`🎯 Target Lock ativado! Fixando '${sneakerData.name}' no radar...`, true);

          pinBtn.textContent = "📌 FIXADO";
          pinBtn.classList.add("pinned");
          pinBtn.disabled = true;

          await fetch("/api/sneakers/pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(sneakerData)
          });

          currentlyPinnedIds.add(sneakerData.id);
          await loadDashboardData();
        });
      }

      searchResultsContainer.appendChild(card);
    });
  }

  // Action Buttons
  if (btnCollect) {
    btnCollect.addEventListener("click", async () => {
      btnCollect.disabled = true;
      logTerminal("Executando varredura manual de preços em todas as fontes...");
      try {
        const res = await fetch("/api/collect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mock: true })
        });
        const data = await res.json();
        logTerminal(`Varredura concluída com ${data.collected_records} leituras coletadas.`);
        await loadDashboardData();
      } catch (e) {
        logTerminal(`Erro ao executar coleta: ${e.message}`, true);
      } finally {
        btnCollect.disabled = false;
      }
    });
  }

  if (btnSeed) {
    btnSeed.addEventListener("click", async () => {
      btnSeed.disabled = true;
      logTerminal("Populando banco de dados com 30 dias de dados simulados...");
      try {
        await fetch("/api/seed", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ days: 30 })
        });
        logTerminal("Banco populado com sucesso!");
        await loadDashboardData();
      } catch (e) {
        logTerminal(`Erro ao gerar seed: ${e.message}`, true);
      } finally {
        btnSeed.disabled = false;
      }
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      loadDashboardData();
    });
  }
});
