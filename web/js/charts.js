/* ==========================================================================
   SNEAKER PULSE COMMAND CENTER - CUSTOM CYBER CHARTS (CHART.JS)
   ========================================================================== */

const SneakerCharts = (function () {
  let historyChart = null;
  let comparisonChart = null;

  // Chart.js Default Dark Theme Setup
  if (typeof Chart !== "undefined") {
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    Chart.defaults.color = "#94A3B8";
    Chart.defaults.borderColor = "rgba(255, 255, 255, 0.05)";
  }

  function renderPriceHistory(historyData) {
    const ctx = document.getElementById("priceHistoryChart");
    if (!ctx || !historyData || historyData.length === 0) return;

    if (historyChart) {
      historyChart.destroy();
    }

    // Processa timestamps e preços por modelo
    const timestamps = [...new Set(historyData.map(d => d.timestamp))].sort();
    const sneakersGrouped = {};

    historyData.forEach(item => {
      if (!sneakersGrouped[item.sneaker_name]) {
        sneakersGrouped[item.sneaker_name] = {};
      }
      sneakersGrouped[item.sneaker_name][item.timestamp] = item.price;
    });

    const colors = ["#ff1e42", "#00f0ff", "#f59e0b", "#10b981", "#8b5cf6"];
    const datasets = Object.keys(sneakersGrouped).map((sneakerName, idx) => {
      const color = colors[idx % colors.length];
      const dataPoints = timestamps.map(ts => sneakersGrouped[sneakerName][ts] || null);

      return {
        label: sneakerName,
        data: dataPoints,
        borderColor: color,
        backgroundColor: color.replace(")", ", 0.1)").replace("rgb", "rgba").replace("#ff1e42", "rgba(255, 30, 66, 0.1)"),
        borderWidth: 2.5,
        tension: 0.35,
        pointBackgroundColor: color,
        pointBorderColor: "#060709",
        pointHoverRadius: 6,
        fill: idx === 0
      };
    });

    historyChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: timestamps.map(ts => ts.substring(5, 16)),
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              usePointStyle: true,
              boxWidth: 8,
              font: { family: "'Orbitron', sans-serif", size: 11 }
            }
          },
          tooltip: {
            backgroundColor: "rgba(12, 14, 20, 0.95)",
            borderColor: "rgba(255, 30, 66, 0.4)",
            borderWidth: 1,
            titleFont: { family: "'Orbitron', sans-serif", size: 12 },
            bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
            padding: 12,
            callbacks: {
              label: function (context) {
                return ` ${context.dataset.label}: R$ ${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 30, 66, 0.05)" },
            ticks: { font: { size: 10 } }
          },
          y: {
            grid: { color: "rgba(255, 30, 66, 0.08)" },
            ticks: {
              font: { size: 11 },
              callback: value => `R$ ${value}`
            }
          }
        }
      }
    });
  }

  function renderSourceComparison(summariesData) {
    const ctx = document.getElementById("sourceComparisonChart");
    if (!ctx || !summariesData || summariesData.length === 0) return;

    if (comparisonChart) {
      comparisonChart.destroy();
    }

    const labels = summariesData.map(s => s.name);
    const currentPrices = summariesData.map(s => s.current_best_price);
    const targetPrices = summariesData.map(s => s.target_price);

    comparisonChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Menor Preço Atual",
            data: currentPrices,
            backgroundColor: "rgba(255, 30, 66, 0.8)",
            borderColor: "#ff1e42",
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: "Preço Alvo",
            data: targetPrices,
            backgroundColor: "rgba(0, 240, 255, 0.3)",
            borderColor: "#00f0ff",
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              font: { family: "'Orbitron', sans-serif", size: 10 }
            }
          },
          tooltip: {
            backgroundColor: "rgba(12, 14, 20, 0.95)",
            borderColor: "rgba(255, 30, 66, 0.4)",
            borderWidth: 1,
            callbacks: {
              label: function (context) {
                return ` ${context.dataset.label}: R$ ${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { size: 10 } }
          },
          y: {
            grid: { color: "rgba(255, 30, 66, 0.08)" },
            ticks: {
              font: { size: 10 },
              callback: value => `R$ ${value}`
            }
          }
        }
      }
    });
  }

  return {
    renderPriceHistory,
    renderSourceComparison
  };
})();
