let pageData = null;
let historyChart = null;
let votesTrendChart = null;
let topReachChart = null;
let sortConfig = { key: "rank", direction: "asc" };

const tableBody = document.querySelector("#ranking-table tbody");
const tableHead = document.querySelector("#ranking-table thead");
const pollsTableBody = document.querySelector("#polls-table tbody");
const standText = document.querySelector("#stand-text");
const emptyState = document.querySelector("#empty-state");
const rankingSection = document.querySelector("#ranking-title").closest("section");
const historySection = document.querySelector("#history-title").closest("section");
const engagementSection = document.querySelector("#engagement-title").closest("section");
const episodeSelect = document.querySelector("#episode-select");
const historyMeta = document.querySelector("#history-meta");
const metadataWarning = document.querySelector("#metadata-warning");
const metadataWarningText = document.querySelector("#metadata-warning p");
const environmentBanner = document.querySelector("#environment-banner");
const environmentBannerTitle = document.querySelector("#environment-banner-title");
const environmentBannerText = document.querySelector("#environment-banner-text");

const kpiRanked = document.querySelector("#kpi-ranked");
const kpiOpenPolls = document.querySelector("#kpi-open-polls");
const kpiTotalVotes = document.querySelector("#kpi-total-votes");
const kpiVotesPerPoll = document.querySelector("#kpi-votes-per-poll");
const kpiStdError = document.querySelector("#kpi-std-error");
const kpiCoverage = document.querySelector("#kpi-coverage");

const openPollsList = document.querySelector("#open-polls-list");
const nextPairsList = document.querySelector("#next-pairs-list");
const topExcitingList = document.querySelector("#top-exciting-list");
const topReachCanvas = document.querySelector("#top-reach-chart");
const episodeEngagementGrid = document.querySelector("#episode-engagement-grid");
const themeSelect = document.querySelector("#theme-select");
const accentPresetButtons = Array.from(document.querySelectorAll(".accent-swatch"));
const accentPresetsContainer = document.querySelector("#accent-presets");

const ACCENT_PRESETS = {
  amber: true,
  blue: true,
  teal: true,
  green: true,
  red: true,
  indigo: true,
};

function getEpisodeMetadata(episodeId) {
  return pageData.episode_metadata_by_id?.[String(episodeId)] || null;
}

function getEpisodeTitle(episodeId) {
  const metadata = getEpisodeMetadata(episodeId);
  return metadata?.title?.trim() || `Episode #${episodeId}`;
}

function getEpisodeLabel(episodeId) {
  return `#${episodeId} - ${getEpisodeTitle(episodeId)}`;
}

function formatNumber(value, digits = 4) {
  return Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatInteger(value) {
  return Number(value || 0).toLocaleString("de-DE");
}

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return "-";
  }

  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date) + " UTC";
}

function formatDate(timestamp) {
  if (!timestamp) {
    return "-";
  }

  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date);
}

function episodeAnchor(episodeId) {
  return `<a href="#episode-card-${episodeId}" class="episode-link">#${episodeId}</a>`;
}

function voteSplitBar(votesA, votesB) {
  const total = votesA + votesB;
  const pctA = total > 0 ? (votesA / total) * 100 : 0;
  const pctB = 100 - pctA;
  return `
    <div class="mini-progress" role="img" aria-label="Stimmenverteilung Folge A ${votesA} zu Folge B ${votesB}">
      <span class="mini-progress-a" style="width:${pctA.toFixed(2)}%"></span>
      <span class="mini-progress-b" style="width:${pctB.toFixed(2)}%"></span>
    </div>
  `;
}

function totalVotesBar(totalVotes, maxVotes) {
  const pct = maxVotes > 0 ? (totalVotes / maxVotes) * 100 : 0;
  return `
    <div class="mini-total-bar" role="img" aria-label="Gesamtstimmen ${totalVotes} von maximal ${maxVotes}">
      <span style="width:${pct.toFixed(2)}%"></span>
    </div>
  `;
}

function formatMaybeNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function cssColorVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function resolveTheme(themePreference) {
  if (themePreference === "dark" || themePreference === "light") {
    return themePreference;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredThemePreference() {
  const value = localStorage.getItem("dashboard-theme");
  return value === "light" || value === "dark" || value === "system" ? value : "system";
}

function getStoredAccentPreset() {
  const value = localStorage.getItem("dashboard-accent");
  return ACCENT_PRESETS[value] ? value : "amber";
}

function updateAccentPresetSelection(accentPreset) {
  for (const button of accentPresetButtons) {
    button.classList.toggle("is-active", button.dataset.accent === accentPreset);
    button.setAttribute("aria-checked", button.dataset.accent === accentPreset ? "true" : "false");
  }
}

function applyThemePreference(themePreference) {
  const resolvedTheme = resolveTheme(themePreference);
  document.documentElement.dataset.theme = resolvedTheme;
  localStorage.setItem("dashboard-theme", themePreference);
  if (themeSelect) {
    themeSelect.value = themePreference;
  }
}

function applyAccentPreset(accentPreset) {
  const selectedAccent = ACCENT_PRESETS[accentPreset] ? accentPreset : "amber";
  const root = document.documentElement;
  root.dataset.accent = selectedAccent;
  localStorage.setItem("dashboard-accent", selectedAccent);
  updateAccentPresetSelection(selectedAccent);
}

function refreshChartsForAppearanceChange() {
  if (!pageData) {
    return;
  }
  renderTopPollCharts();
  renderVotesTrendChart();
  if (pageData.has_rankings && episodeSelect?.value) {
    renderHistoryChart(episodeSelect.value);
  }
}

function initializeAppearanceSettings() {
  const themePreference = getStoredThemePreference();
  const accentPreset = getStoredAccentPreset();
  applyThemePreference(themePreference);
  applyAccentPreset(accentPreset);

  if (themeSelect) {
    themeSelect.addEventListener("change", () => {
      applyThemePreference(themeSelect.value);
      refreshChartsForAppearanceChange();
    });
  }

  if (accentPresetsContainer) {
    accentPresetsContainer.addEventListener("click", (event) => {
      const button = event.target.closest(".accent-swatch");
      if (!button) {
        return;
      }
      applyAccentPreset(button.dataset.accent || "amber");
      refreshChartsForAppearanceChange();
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (getStoredThemePreference() === "system") {
      applyThemePreference("system");
      refreshChartsForAppearanceChange();
    }
  });
}

function renderMetadataWarning() {
  if (!pageData.metadata_warning) {
    metadataWarning.classList.add("hidden");
    return;
  }

  metadataWarningText.innerHTML = `${pageData.metadata_warning} <a href="https://api.dreimetadaten.de/" target="_blank" rel="noopener noreferrer">Dreimetadaten API</a>`;
  metadataWarning.classList.remove("hidden");
}

function renderEnvironmentBanner() {
  const banner = pageData.environment_banner;
  if (!banner || !banner.title || !banner.text) {
    environmentBanner.classList.add("hidden");
    return;
  }

  environmentBannerTitle.textContent = banner.title;
  environmentBannerText.textContent = banner.text;
  environmentBanner.classList.remove("hidden");
}

function renderKPIs() {
  const kpis = pageData.kpis || {};
  const avgVotes = formatMaybeNumber(kpis.avg_votes_per_poll, 0);
  const medianVotes = formatMaybeNumber(kpis.median_votes_per_poll, 0);
  const knownEpisodeCount = Number(kpis.known_episode_count || 0);
  const coverageRatio = kpis.coverage_ratio;
  const coveragePercent = coverageRatio === null || coverageRatio === undefined
    ? "-"
    : `${formatMaybeNumber(Number(coverageRatio) * 100.0, 1)} %`;
  const coverageText = knownEpisodeCount > 0
    ? `${coveragePercent} (${formatInteger(kpis.ranked_episodes ?? 0)}/${formatInteger(knownEpisodeCount)})`
    : "-";

  kpiRanked.textContent = String(kpis.ranked_episodes ?? pageData.ranking.length ?? 0);
  kpiOpenPolls.textContent = String(kpis.open_polls ?? pageData.open_polls?.length ?? 0);
  kpiTotalVotes.textContent = formatInteger(kpis.total_votes ?? 0);
  kpiVotesPerPoll.textContent = `Ø ${avgVotes} | Median ${medianVotes}`;
  kpiStdError.textContent = formatMaybeNumber(kpis.avg_std_error, 3);
  kpiCoverage.textContent = coverageText;
}

function renderOpenPolls() {
  const polls = pageData.open_polls || [];
  openPollsList.innerHTML = "";

  if (!polls.length) {
    openPollsList.innerHTML = '<p class="hint">Aktuell keine offenen Umfragen.</p>';
    return;
  }

  for (const poll of polls) {
    const item = document.createElement("article");
    item.className = "next-pair-card open-poll-card";

    let badgeClass = "badge";
    let badgeLabel = "offen";
    if (poll.status === "pending_finalization") {
      badgeClass = "badge is-pending";
      badgeLabel = "überfällig";
    } else if (poll.status === "unknown_close") {
      badgeClass = "badge is-unknown";
      badgeLabel = "ohne Ablauf";
    }

    const closesText = poll.closes_at
      ? `Schließt: ${formatTimestamp(poll.closes_at)}`
      : "Schließzeit unbekannt";

    const leftMeta = getEpisodeMetadata(poll.episode_a_id);
    const rightMeta = getEpisodeMetadata(poll.episode_b_id);
    const leftCover = leftMeta?.cover_url
      ? `<img class="next-pair-cover" src="${leftMeta.cover_url}" alt="Cover Episode #${poll.episode_a_id}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${poll.episode_a_id}</div>`;
    const rightCover = rightMeta?.cover_url
      ? `<img class="next-pair-cover" src="${rightMeta.cover_url}" alt="Cover Episode #${poll.episode_b_id}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${poll.episode_b_id}</div>`;

    item.innerHTML = `
      <div class="next-pair-vs-row">
        <div class="next-pair-episode">
          ${leftCover}
          <p class="next-pair-title">${getEpisodeLabel(poll.episode_a_id)}</p>
        </div>
        <div class="next-pair-vs">VS</div>
        <div class="next-pair-episode">
          ${rightCover}
          <p class="next-pair-title">${getEpisodeLabel(poll.episode_b_id)}</p>
        </div>
      </div>
      <div class="next-pair-meta">
        <p class="list-sub">Poll #${poll.poll_id} - ${closesText}</p>
        <span class="${badgeClass}">${badgeLabel}</span>
      </div>
    `;
    openPollsList.appendChild(item);
  }
}

function renderNextPairs() {
  const candidates = pageData.next_match_candidates || [];
  nextPairsList.innerHTML = "";

  if (!candidates.length) {
    nextPairsList.innerHTML = '<p class="hint">Derzeit keine Kandidaten berechenbar.</p>';
    return;
  }

  for (const candidate of candidates) {
    const item = document.createElement("article");
    item.className = "next-pair-card";
    const leftMeta = getEpisodeMetadata(candidate.episode_a_id);
    const rightMeta = getEpisodeMetadata(candidate.episode_b_id);
    const leftCover = leftMeta?.cover_url
      ? `<img class="next-pair-cover" src="${leftMeta.cover_url}" alt="Cover Episode #${candidate.episode_a_id}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${candidate.episode_a_id}</div>`;
    const rightCover = rightMeta?.cover_url
      ? `<img class="next-pair-cover" src="${rightMeta.cover_url}" alt="Cover Episode #${candidate.episode_b_id}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${candidate.episode_b_id}</div>`;
    const scoreLabel = candidate.is_seed_phase ? "Seed-Phase" : `Score ${formatMaybeNumber(candidate.score, 3)}`;
    const reasonLabel = candidate.reason || "Priorität aus Matchmaking-Score";

    item.innerHTML = `
      <div class="next-pair-vs-row">
        <div class="next-pair-episode">
          ${leftCover}
          <p class="next-pair-title">${getEpisodeLabel(candidate.episode_a_id)}</p>
        </div>
        <div class="next-pair-vs">VS</div>
        <div class="next-pair-episode">
          ${rightCover}
          <p class="next-pair-title">${getEpisodeLabel(candidate.episode_b_id)}</p>
        </div>
      </div>
      <div class="next-pair-meta">
        <p class="list-sub">${scoreLabel} - ${reasonLabel}</p>
        <span class="badge">prognose</span>
      </div>
    `;
    nextPairsList.appendChild(item);
  }
}

function renderPollsTable() {
  const polls = pageData.all_polls || [];
  pollsTableBody.innerHTML = "";
  const maxVotes = polls.reduce((maxValue, poll) => Math.max(maxValue, poll.total_votes || 0), 0);

  if (!polls.length) {
    pollsTableBody.innerHTML = '<tr><td colspan="8">Keine Umfragen vorhanden.</td></tr>';
    return;
  }

  for (const poll of polls) {
    const tr = document.createElement("tr");
    const statusClass = poll.status === "finalized"
      ? "badge is-finalized"
      : poll.status === "pending_finalization"
        ? "badge is-pending"
        : poll.status === "unknown_close"
          ? "badge is-unknown"
          : "badge";

    const statusLabel = poll.status === "finalized"
      ? "finalisiert"
      : poll.status === "pending_finalization"
        ? "überfällig"
        : poll.status === "unknown_close"
          ? "ohne Ablauf"
          : "offen";

    tr.innerHTML = `
      <td>#${poll.poll_id}</td>
      <td><span class="${statusClass}">${statusLabel}</span></td>
      <td>${episodeAnchor(poll.episode_a_id)}</td>
      <td>${episodeAnchor(poll.episode_b_id)}</td>
      <td>
        <div class="poll-stimmen-cell">
          <span>A ${formatInteger(poll.votes_a)} : B ${formatInteger(poll.votes_b)}</span>
          ${voteSplitBar(poll.votes_a, poll.votes_b)}
        </div>
      </td>
      <td>
        <div class="poll-gesamt-cell">
          <span>${formatInteger(poll.total_votes)}</span>
          ${totalVotesBar(poll.total_votes, maxVotes)}
        </div>
      </td>
      <td>${formatInteger(poll.vote_margin)}</td>
      <td>${formatDate(poll.finalized_at || poll.closes_at)}</td>
    `;
    pollsTableBody.appendChild(tr);
  }
}

function renderTopExcitingList() {
  const polls = pageData.top_exciting_polls || [];
  topExcitingList.innerHTML = "";

  if (!polls.length) {
    topExcitingList.innerHTML = '<p class="hint">Noch keine finalisierten Umfragen vorhanden.</p>';
    return;
  }

  for (const poll of polls) {
    const row = document.createElement("article");
    row.className = "mini-poll-row";
    const metaA = getEpisodeMetadata(poll.episode_a_id);
    const metaB = getEpisodeMetadata(poll.episode_b_id);
    const coverA = metaA?.cover_url
      ? `<img class="mini-cover" src="${metaA.cover_url}" alt="Cover Episode #${poll.episode_a_id}">`
      : `<div class="mini-cover mini-cover-fallback">#${poll.episode_a_id}</div>`;
    const coverB = metaB?.cover_url
      ? `<img class="mini-cover" src="${metaB.cover_url}" alt="Cover Episode #${poll.episode_b_id}">`
      : `<div class="mini-cover mini-cover-fallback">#${poll.episode_b_id}</div>`;
    const avgRank = poll.avg_pair_rank ? ` | Ø Rang ${formatMaybeNumber(poll.avg_pair_rank, 1)}` : "";

    row.innerHTML = `
      <div class="mini-pair-covers">${coverA}<span>VS</span>${coverB}</div>
      <div class="mini-pair-text">
        <strong>${episodeAnchor(poll.episode_a_id)} vs ${episodeAnchor(poll.episode_b_id)}</strong>
        <p class="list-sub">A ${formatInteger(poll.votes_a)} : B ${formatInteger(poll.votes_b)} | Gesamt ${formatInteger(poll.total_votes)} | Margin ${formatInteger(poll.vote_margin)}${avgRank}</p>
        ${voteSplitBar(poll.votes_a, poll.votes_b)}
      </div>
    `;
    topExcitingList.appendChild(row);
  }
}

function renderTopPollChart(canvas, existingChart, polls, title, mode = "absolute") {
  if (existingChart) {
    existingChart.destroy();
  }

  if (!polls.length) {
    return null;
  }

  const labels = polls.map((poll) => `#${poll.episode_a_id} vs #${poll.episode_b_id}`);
  const datasetA = polls.map((poll) => {
    if (mode === "percent") {
      return poll.total_votes > 0 ? (poll.votes_a / poll.total_votes) * 100.0 : 0;
    }
    return poll.votes_a;
  });
  const datasetB = polls.map((poll) => {
    if (mode === "percent") {
      return poll.total_votes > 0 ? (poll.votes_b / poll.total_votes) * 100.0 : 0;
    }
    return poll.votes_b;
  });

  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Folge A",
          data: datasetA,
          backgroundColor: cssColorVar("--chart-a-fill"),
          borderColor: cssColorVar("--chart-a"),
          borderWidth: 1,
          borderRadius: 0,
          borderSkipped: false,
        },
        {
          label: "Folge B",
          data: datasetB,
          backgroundColor: cssColorVar("--chart-b-fill"),
          borderColor: cssColorVar("--chart-b"),
          borderWidth: 1,
          borderRadius: 0,
          borderSkipped: false,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            title(items) {
              const item = items[0];
              const poll = polls[item.dataIndex];
              return `${title}: #${poll.episode_a_id} vs #${poll.episode_b_id}`;
            },
            label(context) {
              const poll = polls[context.dataIndex];
              const rankInfo = poll.avg_pair_rank ? ` | Ø Rang ${formatMaybeNumber(poll.avg_pair_rank, 1)}` : "";
              const split = `A ${formatInteger(poll.votes_a)} : B ${formatInteger(poll.votes_b)}`;
              const ratio = poll.total_votes > 0
                ? ` (${formatMaybeNumber((poll.votes_a / poll.total_votes) * 100.0, 1)}% : ${formatMaybeNumber((poll.votes_b / poll.total_votes) * 100.0, 1)}%)`
                : "";
              return `${split}${ratio} | Gesamt ${formatInteger(poll.total_votes)} | Margin ${formatInteger(poll.vote_margin)}${rankInfo}`;
            },
            afterLabel(context) {
              const poll = polls[context.dataIndex];
              return `#${poll.episode_a_id} vs #${poll.episode_b_id}`;
            },
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          beginAtZero: true,
          max: mode === "percent" ? 100 : undefined,
          title: {
            display: true,
            text: mode === "percent" ? "Stimmenanteil in %" : "Stimmen (A + B)",
          },
        },
        y: {
          stacked: true,
        },
      },
    },
  });
}

function renderTopPollCharts() {
  const reach = pageData.top_reach_polls || [];
  topReachChart = renderTopPollChart(topReachCanvas, topReachChart, reach, "Reichweite", "absolute");
  renderTopExcitingList();
}

function computeRollingAverage(values, windowSize = 7) {
  const result = [];
  for (let index = 0; index < values.length; index += 1) {
    const start = Math.max(0, index - windowSize + 1);
    const subset = values.slice(start, index + 1);
    const avg = subset.reduce((sum, value) => sum + value, 0) / subset.length;
    result.push(avg);
  }
  return result;
}

function renderVotesTrendChart() {
  const trend = pageData.votes_trend || [];
  if (votesTrendChart) {
    votesTrendChart.destroy();
    votesTrendChart = null;
  }

  if (!trend.length) {
    return;
  }

  const labels = trend.map((entry) => `#${entry.poll_id} - ${formatTimestamp(entry.finalized_at)}`);
  const votes = trend.map((entry) => entry.total_votes);
  const rollingAverage = computeRollingAverage(votes, 7);
  const pointColors = trend.map((entry) => {
    if (!entry.avg_pair_rank || Number.isNaN(Number(entry.avg_pair_rank))) {
      return cssColorVar("--chart-line");
    }
    return entry.avg_pair_rank <= 10 ? cssColorVar("--chart-a") : cssColorVar("--chart-line-secondary");
  });

  votesTrendChart = new Chart(document.querySelector("#votes-trend-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Gesamtstimmen",
          data: votes,
          borderColor: cssColorVar("--chart-line"),
          backgroundColor: cssColorVar("--chart-line-fill"),
          pointBackgroundColor: pointColors,
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.25,
        },
        {
          label: "7-Umfragen-Mittel",
          data: rollingAverage,
          borderColor: cssColorVar("--chart-line-secondary"),
          backgroundColor: cssColorVar("--chart-line-secondary-fill"),
          borderDash: [6, 4],
          pointRadius: 0,
          tension: 0.25,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label(context) {
              if (context.dataset.label !== "Gesamtstimmen") {
                return `${context.dataset.label}: ${formatMaybeNumber(context.raw, 1)}`;
              }
              const poll = trend[context.dataIndex];
              const rankInfo = poll.avg_pair_rank ? ` | Ø Rang ${formatMaybeNumber(poll.avg_pair_rank, 1)}` : "";
              return `Stimmen ${formatInteger(poll.total_votes)}${rankInfo}`;
            },
          },
        },
      },
      scales: {
        y: {
          title: {
            display: true,
            text: "Gesamtstimmen",
          },
        },
      },
    },
  });
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
    const metadata = getEpisodeMetadata(row.episode_id);
    const title = metadata?.title ? metadata.title : "Keine Metadaten";
    const cover = metadata?.cover_url
      ? `<img class="episode-cover" src="${metadata.cover_url}" alt="Cover Episode #${row.episode_id}">`
      : "";

    tr.innerHTML = `
      <td>${row.rank}</td>
      <td>#${row.episode_id}</td>
      <td class="episode-title"><span class="episode-meta">${cover}<span>${title}</span></span></td>
      <td>${formatNumber(row.utility)}</td>
      <td>${formatNumber(row.std_error)}</td>
      <td>${formatInteger(row.poll_count)}</td>
      <td><button type="button" class="icon-button" data-episode-id="${row.episode_id}" title="Verlauf für Episode #${row.episode_id}" aria-label="Verlauf für Episode #${row.episode_id}"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 19h18v2H3zm2-4 4-4 3 3 5-7 2 1-6 9-3-3-3 3z"/></svg></button></td>
    `;
    tableBody.appendChild(tr);
  }

  for (const button of tableBody.querySelectorAll(".icon-button")) {
    button.addEventListener("click", () => {
      setEpisodeInChart(button.dataset.episodeId);
    });
  }
}

function renderEpisodeEngagementCards() {
  const cards = pageData.episode_engagement_cards || [];
  episodeEngagementGrid.innerHTML = "";

  if (!cards.length) {
    episodeEngagementGrid.innerHTML = '<p class="hint">Noch keine Folgen-Engagementdaten vorhanden.</p>';
    return;
  }

  for (const card of cards) {
    const metadata = getEpisodeMetadata(card.episode_id);
    const cover = metadata?.cover_url
      ? `<img class="engagement-hero" src="${metadata.cover_url}" alt="Cover Episode #${card.episode_id}">`
      : `<div class="engagement-hero engagement-cover-fallback">#${card.episode_id}</div>`;

    const item = document.createElement("article");
    item.className = "engagement-card";
    item.id = `episode-card-${card.episode_id}`;
    item.innerHTML = `
      ${cover}
      <div class="engagement-header">
        <div>
          <p class="engagement-rank">Rang ${card.rank}</p>
          <h3>${getEpisodeLabel(card.episode_id)}</h3>
        </div>
      </div>
      <div class="engagement-metrics">
        <p><span>Utility</span><strong>${formatNumber(card.utility)}</strong></p>
        <p><span>Unsicherheit</span><strong>${formatNumber(card.std_error)}</strong></p>
        <p><span>Umfragen</span><strong>${formatInteger(card.poll_count)}</strong></p>
        <p><span>Ø Stimmen/Umfrage</span><strong>${formatMaybeNumber(card.avg_votes_per_poll, 1)}</strong></p>
        <p><span>Median Stimmen/Umfrage</span><strong>${formatMaybeNumber(card.median_votes_per_poll, 1)}</strong></p>
        <p><span>Stimmen gesamt</span><strong>${formatInteger(card.total_votes)}</strong></p>
      </div>
    `;
    episodeEngagementGrid.appendChild(item);
  }
}

function renderEpisodeSelect() {
  episodeSelect.innerHTML = "";
  for (const episodeId of pageData.episode_ids) {
    const option = document.createElement("option");
    option.value = String(episodeId);
    option.textContent = getEpisodeLabel(episodeId);
    episodeSelect.appendChild(option);
  }

  episodeSelect.addEventListener("change", () => {
    renderHistoryChart(episodeSelect.value);
  });
}

function renderHistoryChart(episodeIdString) {
  const history = pageData.history_by_episode[episodeIdString] || [];
  if (!history.length) {
    historyMeta.textContent = `Keine Historie für Episode #${episodeIdString} vorhanden.`;
    if (historyChart) {
      historyChart.destroy();
      historyChart = null;
    }
    return;
  }

  const labels = history.map((entry) => formatTimestamp(entry.calculated_at));
  const utilityData = history.map((entry) => entry.utility);
  const lowerData = history.map((entry) => entry.utility - entry.std_error);
  const upperData = history.map((entry) => entry.utility + entry.std_error);
  const latestEntry = history[history.length - 1];
  historyMeta.textContent = `${getEpisodeLabel(episodeIdString)}: ${history.length} Snapshot(s), letzter Stand ${formatTimestamp(latestEntry.calculated_at)}.`;

  if (historyChart) {
    historyChart.destroy();
  }

  historyChart = new Chart(document.querySelector("#history-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Untergrenze",
          data: lowerData,
          borderColor: "rgba(0, 0, 0, 0)",
          pointRadius: 0,
        },
        {
          label: "Unsicherheit",
          data: upperData,
          borderColor: "rgba(0, 0, 0, 0)",
          backgroundColor: cssColorVar("--chart-band-fill"),
          fill: "-1",
          pointRadius: 0,
        },
        {
          label: "Utility",
          data: utilityData,
          borderColor: cssColorVar("--chart-line"),
          backgroundColor: cssColorVar("--chart-line"),
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
  engagementSection.classList.remove("hidden");

  renderMetadataWarning();
  renderEnvironmentBanner();
  renderKPIs();
  renderOpenPolls();
  renderNextPairs();
  renderPollsTable();
  renderTopPollCharts();
  renderVotesTrendChart();
  renderEpisodeEngagementCards();
  setupSorting();
  renderTable();
  renderEpisodeSelect();
  renderHistoryChart(String(pageData.episode_ids[0]));
}

function renderEmptyState() {
  standText.textContent = "Es sind noch keine gerankten Episoden vorhanden.";
  rankingSection.classList.add("hidden");
  historySection.classList.add("hidden");
  engagementSection.classList.add("hidden");
  emptyState.classList.remove("hidden");

  renderMetadataWarning();
  renderEnvironmentBanner();
  renderKPIs();
  renderOpenPolls();
  renderNextPairs();
  renderPollsTable();
  renderTopPollCharts();
  renderVotesTrendChart();
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

initializeAppearanceSettings();
init();
