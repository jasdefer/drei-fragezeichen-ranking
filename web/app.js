let pageData = null;
let chart = null;
let sortConfig = { key: "rank", direction: "asc" };

const tableBody = document.querySelector("#ranking-table tbody");
const tableHead = document.querySelector("#ranking-table thead");
const standText = document.querySelector("#stand-text");
const emptyState = document.querySelector("#empty-state");
const rankingSection = document.querySelector("#ranking-title").closest("section");
const historySection = document.querySelector("#history-title").closest("section");
const episodeSelect = document.querySelector("#episode-select");
const historyMeta = document.querySelector("#history-meta");

function formatNumber(value, digits = 4) {
  return Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date) + " UTC";
}

function sortedRanking() {
  const rows = [...pageData.ranking];
  const { key, direction } = sortConfig;

  rows.sort((a, b) => {
    const left = a[key];
    const right = b[key];

    if (typeof left === "number" && typeof right === "number") {
      return direction === "asc" ? left - right : right - left;
    }

    return direction === "asc"
      ? String(left).localeCompare(String(right), "de")
      : String(right).localeCompare(String(left), "de");
  });

  return rows;
}

function setEpisodeInChart(episodeId) {
  episodeSelect.value = String(episodeId);
  renderHistoryChart(String(episodeId));
  historySection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderTable() {
  const rows = sortedRanking();
  tableBody.innerHTML = "";

  for (const row of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.rank}</td>
      <td>#${row.episode_id}</td>
      <td>${formatNumber(row.utility)}</td>
      <td>${formatNumber(row.std_error)}</td>
      <td>${row.matches}</td>
      <td><button type="button" class="link-button" data-episode-id="${row.episode_id}">Verlauf anzeigen</button></td>
    `;
    tableBody.appendChild(tr);
  }

  for (const button of tableBody.querySelectorAll(".link-button")) {
    button.addEventListener("click", () => {
      setEpisodeInChart(button.dataset.episodeId);
    });
  }
}

function renderEpisodeSelect() {
  episodeSelect.innerHTML = "";
  for (const episodeId of pageData.episode_ids) {
    const option = document.createElement("option");
    option.value = String(episodeId);
    option.textContent = `#${episodeId}`;
    episodeSelect.appendChild(option);
  }

  episodeSelect.addEventListener("change", () => {
    renderHistoryChart(episodeSelect.value);
  });
}

function renderHistoryChart(episodeIdString) {
  const history = pageData.history_by_episode[episodeIdString] || [];

  if (!history.length) {
    historyMeta.textContent = `Keine Historie fuer Episode #${episodeIdString} vorhanden.`;
    if (chart) {
      chart.destroy();
      chart = null;
    }
    return;
  }

  const labels = history.map((entry) => formatTimestamp(entry.calculated_at));
  const utilityData = history.map((entry) => entry.utility);
  const lowerData = history.map((entry) => entry.utility - entry.std_error);
  const upperData = history.map((entry) => entry.utility + entry.std_error);

  const latestEntry = history[history.length - 1];
  historyMeta.textContent = `Episode #${episodeIdString}: ${history.length} Snapshot(s), letzter Stand ${formatTimestamp(latestEntry.calculated_at)}.`;

  if (chart) {
    chart.destroy();
  }

  const context = document.getElementById("history-chart");
  chart = new Chart(context, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Untergrenze",
          data: lowerData,
          borderColor: "rgba(251, 192, 45, 0)",
          pointRadius: 0,
        },
        {
          label: "Unsicherheit",
          data: upperData,
          borderColor: "rgba(251, 192, 45, 0)",
          backgroundColor: "rgba(251, 192, 45, 0.30)",
          fill: "-1",
          pointRadius: 0,
        },
        {
          label: "Utility",
          data: utilityData,
          borderColor: "#7a5f00",
          backgroundColor: "#7a5f00",
          borderWidth: 2,
          tension: 0.25,
          pointRadius: 3,
          pointHoverRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          labels: {
            filter(item) {
              return item.text !== "Untergrenze";
            },
          },
        },
        tooltip: {
          callbacks: {
            label(context) {
              if (context.dataset.label === "Unsicherheit") {
                return "Unsicherheitsband";
              }
              return `${context.dataset.label}: ${formatNumber(context.raw)}`;
            },
          },
        },
      },
      scales: {
        y: {
          title: {
            display: true,
            text: "Utility",
          },
        },
      },
    },
  });
}

function setupSorting() {
  tableHead.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-sort]");
    if (!button) {
      return;
    }

    const key = button.dataset.sort;
    if (sortConfig.key === key) {
      sortConfig.direction = sortConfig.direction === "asc" ? "desc" : "asc";
    } else {
      sortConfig.key = key;
      sortConfig.direction = key === "rank" ? "asc" : "desc";
    }
    renderTable();
  });
}

function renderLoadedState() {
  standText.textContent = `Datenstand: ${formatTimestamp(pageData.latest_calculated_at)}.`;
  emptyState.classList.add("hidden");
  rankingSection.classList.remove("hidden");
  historySection.classList.remove("hidden");

  setupSorting();
  renderTable();
  renderEpisodeSelect();
  renderHistoryChart(String(pageData.episode_ids[0]));
}

function renderEmptyState() {
  standText.textContent = "Es sind noch keine gerankten Episoden vorhanden.";
  rankingSection.classList.add("hidden");
  historySection.classList.add("hidden");
  emptyState.classList.remove("hidden");
}

async function init() {
  try {
    const response = await fetch("data/visualization.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    pageData = await response.json();

    if (!pageData.has_rankings) {
      renderEmptyState();
      return;
    }

    renderLoadedState();
  } catch (error) {
    standText.textContent = "Fehler beim Laden der Visualisierungsdaten.";
    console.error(error);
  }
}

init();
