/* ==========================================================================
   SNEAKER PULSE COMMAND CENTER - MAIN CONTROLLER & DATA BINDING
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const bootOverlay = document.getElementById("boot-overlay");
  const bootFill = document.getElementById("boot-fill");
  const lastUpdateTime = document.getElementById("last-update-time");
  const sneakersContainer = document.getElementById("sneakers-container");
  const systemLogContainer = document.getElementById("system-terminal-log");

  // Metric Elements
  const statTotalModels = document.getElementById("stat-total-models");
  const statTargetHits = document.getElementById("stat-target-hits");
  const statAlltimeLows = document.getElementById("stat-alltime-lows");
  const statAvgDiscount = document.getElementById("stat-avg-discount");

  // Buttons
  const btnCollect = document.getElementById("btn-collect");
  const btnSeed = document.getElementById("btn-seed");
  const btnRefresh = document.getElementById("btn-refresh");

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
      logTerminal("Iniciando varredura de telemetria dos dados...");

      const [summaryRes, historyRes] = await Promise.all([
        fetch("/api/summary"),
        fetch("/api/history")
      ]);

      const summaryData = await summaryRes.json();
      const historyData = await historyRes.json();

      renderMetrics(summaryData.summaries, summaryData.alerts);
      renderSneakersGrid(summaryData.summaries);

      if (typeof SneakerCharts !== "undefined") {
        SneakerCharts.renderPriceHistory(historyData);
        SneakerCharts.renderSourceComparison(summaryData.summaries);
      }

      if (summaryData.alerts && summaryData.alerts.length > 0) {
        summaryData.alerts.forEach(a => logTerminal(`🔔 ${a.message}`, true));
      } else {
        logTerminal("Varredura concluída. Todos os sistemas operando normalmente.");
      }

    } catch (err) {
      logTerminal(`❌ Erro ao conectar ao servidor de dados: ${err.message}`, true);
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
          Nenhum tênis cadastrado no momento. Clique em 'Gerar 30D Mock' para testar.
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
          <span class="source-tag">${s.current_best_source}</span>
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
          <span>Menor registrado em ${s.all_time_lowest_date}</span>
        </div>
      `;

      sneakersContainer.appendChild(card);
      if (typeof initCardTilt === "function") {
        initCardTilt(card);
      }
    });
  }

  // Event Listeners
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
