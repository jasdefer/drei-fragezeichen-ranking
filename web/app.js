let pageData = null;
let historyChart = null;
let votesTrendChart = null;
let topReachChart = null;
let coverageGaugeChart = null;
let rankingTable = null;
let pollsTable = null;
let sectionObserver = null;

const standText = document.querySelector("#stand-text");
const emptyState = document.querySelector("#empty-state");
const rankingSection = document.querySelector("#section-ranking");
const historySection = document.querySelector("#section-history");
const engagementSection = document.querySelector("#section-engagement");
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
const kpiCoverageMeta = document.querySelector("#kpi-coverage-meta");

const openPollsList = document.querySelector("#open-polls-list");
const nextPairsList = document.querySelector("#next-pairs-list");
const topExcitingList = document.querySelector("#top-exciting-list");
const topReachCanvas = document.querySelector("#top-reach-chart");
const votesTrendCanvas = document.querySelector("#votes-trend-chart");
const historyCanvas = document.querySelector("#history-chart");
const coverageGaugeCanvas = document.querySelector("#coverage-gauge-chart");
const episodeEngagementGrid = document.querySelector("#episode-engagement-grid");
const themeSelect = document.querySelector("#theme-select");
const accentPresetButtons = Array.from(document.querySelectorAll(".accent-swatch"));
const accentPresetsContainer = document.querySelector("#accent-presets");
const sectionSwitcher = document.querySelector("#mobile-section-switcher");
const sectionSwitcherLinks = Array.from(document.querySelectorAll("#mobile-section-switcher .section-switcher-link"));

const ACCENT_PRESETS = {
  amber: true,
  blue: true,
  teal: true,
  green: true,
  red: true,
  indigo: true,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function cssColorVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

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

function formatMaybeNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatTimestamp(timestamp) {
  if (!timestamp) {
    return "-";
  }

  const date = new Date(timestamp);
  return `${new Intl.DateTimeFormat("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date)} UTC`;
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
  return `<a href="#episode-card-${episodeId}" class="episode-link">#${escapeHtml(episodeId)}</a>`;
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
    const isActive = button.dataset.accent === accentPreset;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-checked", isActive ? "true" : "false");
  }
}

function applyThemePreference(themePreference) {
  const resolvedTheme = resolveTheme(themePreference);
  document.documentElement.setAttribute("data-bs-theme", resolvedTheme);
  localStorage.setItem("dashboard-theme", themePreference);
  if (themeSelect) {
    themeSelect.value = themePreference;
  }
}

function applyAccentPreset(accentPreset) {
  const selectedAccent = ACCENT_PRESETS[accentPreset] ? accentPreset : "amber";
  document.documentElement.dataset.accent = selectedAccent;
  localStorage.setItem("dashboard-accent", selectedAccent);
  updateAccentPresetSelection(selectedAccent);
}

function refreshAppearanceDependentRender() {
  if (!pageData) {
    return;
  }
  renderCoverageGauge();
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
      refreshAppearanceDependentRender();
    });
  }

  if (accentPresetsContainer) {
    accentPresetsContainer.addEventListener("click", (event) => {
      const button = event.target.closest(".accent-swatch");
      if (!button) {
        return;
      }
      applyAccentPreset(button.dataset.accent || "amber");
      refreshAppearanceDependentRender();
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (getStoredThemePreference() === "system") {
      applyThemePreference("system");
      refreshAppearanceDependentRender();
    }
  });
}

function renderMetadataWarning() {
  if (!pageData.metadata_warning) {
    metadataWarning.classList.add("hidden");
    return;
  }
  metadataWarningText.innerHTML = `${escapeHtml(pageData.metadata_warning)} <a href="https://api.dreimetadaten.de/" target="_blank" rel="noopener noreferrer">Dreimetadaten API</a>`;
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

function renderCoverageGauge() {
  if (coverageGaugeChart) {
    coverageGaugeChart.destroy();
    coverageGaugeChart = null;
  }

  const kpis = pageData.kpis || {};
  const ranked = Number(kpis.ranked_episodes || 0);
  const known = Number(kpis.known_episode_count || 0);
  const ratio = known > 0 ? Math.max(0, Math.min(1, ranked / known)) : 0;
  const remaining = Math.max(0, 1 - ratio);

  if (!coverageGaugeCanvas) {
    return;
  }

  coverageGaugeChart = new Chart(coverageGaugeCanvas, {
    type: "doughnut",
    data: {
      labels: ["Gerankt", "Offen"],
      datasets: [{
        data: [ratio, remaining],
        backgroundColor: [cssColorVar("--chart-primary-fill"), "rgba(0,0,0,0.12)"],
        borderColor: [cssColorVar("--chart-primary"), "rgba(0,0,0,0)"],
        borderWidth: 1,
        hoverOffset: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      rotation: -90,
      circumference: 180,
      cutout: "72%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(context) {
              if (context.dataIndex === 0) {
                return `Gerankt: ${formatInteger(ranked)} Folgen`;
              }
              return `Offen: ${formatInteger(Math.max(known - ranked, 0))} Folgen`;
            },
          },
        },
      },
    },
  });
}

function renderKPIs() {
  const kpis = pageData.kpis || {};
  const avgVotes = formatMaybeNumber(kpis.avg_votes_per_poll, 0);
  const medianVotes = formatMaybeNumber(kpis.median_votes_per_poll, 0);
  const knownEpisodeCount = Number(kpis.known_episode_count || 0);
  const rankedEpisodeCount = Number(kpis.ranked_episodes || 0);
  const coveragePercent = knownEpisodeCount > 0
    ? `${formatMaybeNumber((rankedEpisodeCount / knownEpisodeCount) * 100, 1)} %`
    : "-";

  kpiRanked.textContent = formatInteger(rankedEpisodeCount || pageData.ranking?.length || 0);
  kpiOpenPolls.textContent = formatInteger(kpis.open_polls ?? pageData.open_polls?.length ?? 0);
  kpiTotalVotes.textContent = formatInteger(kpis.total_votes ?? 0);
  kpiVotesPerPoll.textContent = `Ø ${avgVotes} | Median ${medianVotes}`;
  kpiStdError.textContent = formatMaybeNumber(kpis.avg_std_error, 3);
  kpiCoverage.textContent = coveragePercent;
  kpiCoverageMeta.textContent = knownEpisodeCount > 0
    ? `${formatInteger(rankedEpisodeCount)}/${formatInteger(knownEpisodeCount)} Folgen`
    : "-";
  renderCoverageGauge();
}

function renderOpenPolls() {
  const polls = pageData.open_polls || [];
  openPollsList.innerHTML = "";

  if (!polls.length) {
    openPollsList.innerHTML = '<div class="col-12"><p class="hint">Aktuell keine offenen Umfragen.</p></div>';
    return;
  }

  for (const poll of polls) {
    const col = document.createElement("div");
    col.className = "col next-pair-col";

    let badgeClass = "status-badge badge rounded-pill";
    let badgeLabel = "offen";
    if (poll.status === "pending_finalization") {
      badgeClass = "status-badge status-pending badge rounded-pill";
      badgeLabel = "überfällig";
    } else if (poll.status === "unknown_close") {
      badgeClass = "status-badge status-unknown badge rounded-pill";
      badgeLabel = "ohne Ablauf";
    }

    const closesText = poll.closes_at ? `Schließt: ${formatTimestamp(poll.closes_at)}` : "Schließzeit unbekannt";
    const leftMeta = getEpisodeMetadata(poll.episode_a_id);
    const rightMeta = getEpisodeMetadata(poll.episode_b_id);
    const leftCover = leftMeta?.cover_url
      ? `<img class="next-pair-cover" src="${escapeHtml(leftMeta.cover_url)}" alt="Cover Episode #${escapeHtml(poll.episode_a_id)}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${escapeHtml(poll.episode_a_id)}</div>`;
    const rightCover = rightMeta?.cover_url
      ? `<img class="next-pair-cover" src="${escapeHtml(rightMeta.cover_url)}" alt="Cover Episode #${escapeHtml(poll.episode_b_id)}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${escapeHtml(poll.episode_b_id)}</div>`;

    col.innerHTML = `
      <article class="next-pair-card h-100">
        <div class="vs-media-strip">
          <div class="row next-pair-vs-row">
            <div class="col next-pair-episode">
              ${leftCover}
            </div>
            <div class="col-auto"><div class="next-pair-vs">VS</div></div>
            <div class="col next-pair-episode">
              ${rightCover}
            </div>
          </div>
        </div>
        <div class="vs-info">
          <p class="vs-match-line">${escapeHtml(getEpisodeLabel(poll.episode_a_id))} <span>vs</span> ${escapeHtml(getEpisodeLabel(poll.episode_b_id))}</p>
          <div class="next-pair-meta">
            <p class="hint">Poll #${escapeHtml(poll.poll_id)} - ${escapeHtml(closesText)}</p>
            <span class="${badgeClass}">${badgeLabel}</span>
          </div>
        </div>
      </article>
    `;
    openPollsList.appendChild(col);
  }
}

function renderNextPairs() {
  const candidates = pageData.next_match_candidates || [];
  nextPairsList.innerHTML = "";

  if (!candidates.length) {
    nextPairsList.innerHTML = '<div class="col-12"><p class="hint">Derzeit keine Kandidaten berechenbar.</p></div>';
    return;
  }

  for (const candidate of candidates) {
    const col = document.createElement("div");
    col.className = "col next-pair-col";
    const leftMeta = getEpisodeMetadata(candidate.episode_a_id);
    const rightMeta = getEpisodeMetadata(candidate.episode_b_id);

    const leftCover = leftMeta?.cover_url
      ? `<img class="next-pair-cover" src="${escapeHtml(leftMeta.cover_url)}" alt="Cover Episode #${escapeHtml(candidate.episode_a_id)}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${escapeHtml(candidate.episode_a_id)}</div>`;

    const rightCover = rightMeta?.cover_url
      ? `<img class="next-pair-cover" src="${escapeHtml(rightMeta.cover_url)}" alt="Cover Episode #${escapeHtml(candidate.episode_b_id)}">`
      : `<div class="next-pair-cover next-pair-cover-fallback">#${escapeHtml(candidate.episode_b_id)}</div>`;

    const scoreLabel = candidate.is_seed_phase
      ? "Seed-Phase"
      : `Score ${formatMaybeNumber(candidate.score, 3)}`;

    col.innerHTML = `
      <article class="next-pair-card h-100">
        <div class="vs-media-strip">
          <div class="row next-pair-vs-row">
            <div class="col next-pair-episode">
              ${leftCover}
            </div>
            <div class="col-auto"><div class="next-pair-vs">VS</div></div>
            <div class="col next-pair-episode">
              ${rightCover}
            </div>
          </div>
        </div>
        <div class="vs-info">
          <p class="vs-match-line">${escapeHtml(getEpisodeLabel(candidate.episode_a_id))} <span>vs</span> ${escapeHtml(getEpisodeLabel(candidate.episode_b_id))}</p>
          <div class="next-pair-meta">
            <p class="hint">${escapeHtml(scoreLabel)} - ${escapeHtml(candidate.reason || "Priorität aus Matchmaking-Score")}</p>
            <span class="status-badge badge rounded-pill">prognose</span>
          </div>
        </div>
      </article>
    `;

    nextPairsList.appendChild(col);
  }
}

function rankingTitleFormatter(cell) {
  const row = cell.getRow().getData();
  const coverHtml = row.cover_url
    ? `<img class="episode-cover" src="${escapeHtml(row.cover_url)}" alt="Cover Episode #${escapeHtml(row.episode_id)}">`
    : `<span class="episode-cover engagement-cover-fallback">#${escapeHtml(row.episode_id)}</span>`;

  return `
    <span class="ranking-title-cell">
      ${coverHtml}
      <span class="ranking-title-text">${escapeHtml(row.title)}</span>
    </span>
  `;
}

function actionFormatter(cell) {
  const row = cell.getRow().getData();
  return `<button type="button" class="icon-button" data-episode-id="${escapeHtml(row.episode_id)}" title="Verlauf für Episode #${escapeHtml(row.episode_id)}" aria-label="Verlauf für Episode #${escapeHtml(row.episode_id)}"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 19h18v2H3zm2-4 4-4 3 3 5-7 2 1-6 9-3-3-3 3z"/></svg></button>`;
}

function initializeRankingTable() {
  const rankingData = (pageData.ranking || []).map((row) => {
    const metadata = getEpisodeMetadata(row.episode_id);
    return {
      ...row,
      title: metadata?.title || "Keine Metadaten",
      cover_url: metadata?.cover_url || null,
      episode_label: `#${row.episode_id}`,
      utility_text: formatNumber(row.utility),
      std_error_text: formatNumber(row.std_error),
      poll_count_text: formatInteger(row.poll_count),
    };
  });

  if (rankingTable) {
    rankingTable.destroy();
  }

  rankingTable = new Tabulator("#ranking-table", {
    data: rankingData,
    layout: "fitColumns",
    responsiveLayout: "collapse",
    responsiveLayoutCollapseStartOpen: false,
    placeholder: "Keine Rankings vorhanden.",
    initialSort: [{ column: "rank", dir: "asc" }],
    columnDefaults: {
      vertAlign: "middle",
      hozAlign: "left",
      headerSortTristate: false,
      headerWordWrap: true,
      minWidth: 90,
    },
    columns: [
      { title: "Rang", field: "rank", sorter: "number", minWidth: 90, widthGrow: 0, responsive: 0 },
      { title: "Episode", field: "episode_id", sorter: "number", formatter: (cell) => `#${cell.getValue()}`, minWidth: 95, widthGrow: 0, responsive: 0 },
      { title: "Titel", field: "title", sorter: "string", formatter: rankingTitleFormatter, minWidth: 260, widthGrow: 4, responsive: 0 },
      { title: "Utility", field: "utility", sorter: "number", formatter: (cell) => formatNumber(cell.getValue()), minWidth: 110, widthGrow: 0, responsive: 2 },
      { title: "Unsicherheit", field: "std_error", sorter: "number", formatter: (cell) => formatNumber(cell.getValue()), minWidth: 130, widthGrow: 0, responsive: 3 },
      { title: "Umfragen", field: "poll_count", sorter: "number", formatter: (cell) => formatInteger(cell.getValue()), minWidth: 100, widthGrow: 0, responsive: 2 },
      {
        title: "Aktion",
        field: "episode_id",
        headerSort: false,
        formatter: actionFormatter,
        minWidth: 90,
        hozAlign: "center",
        widthGrow: 0,
        cellClick(_event, cell) {
          const row = cell.getRow().getData();
          setEpisodeInChart(row.episode_id);
        },
        responsive: 1,
      },
    ],
  });
}

function formatStatusBadge(status) {
  if (status === "finalized") {
    return '<span class="status-badge status-finalized badge rounded-pill">finalisiert</span>';
  }
  if (status === "pending_finalization") {
    return '<span class="status-badge status-pending badge rounded-pill">überfällig</span>';
  }
  if (status === "unknown_close") {
    return '<span class="status-badge status-unknown badge rounded-pill">ohne Ablauf</span>';
  }
  return '<span class="status-badge badge rounded-pill">offen</span>';
}

function initializePollsTable() {
  const polls = pageData.all_polls || [];
  const maxVotes = polls.reduce((maxValue, poll) => Math.max(maxValue, poll.total_votes || 0), 0);
  const pollRows = polls;

  if (pollsTable) {
    pollsTable.destroy();
  }

  pollsTable = new Tabulator("#polls-table", {
    data: pollRows,
    layout: "fitColumns",
    responsiveLayout: "collapse",
    responsiveLayoutCollapseStartOpen: false,
    placeholder: "Keine Umfragen vorhanden.",
    initialSort: [{ column: "poll_id", dir: "desc" }],
    columnDefaults: {
      vertAlign: "middle",
      hozAlign: "left",
      headerSortTristate: false,
      headerWordWrap: true,
      minWidth: 95,
    },
    columns: [
      { title: "Status", field: "status", sorter: "string", formatter: (cell) => formatStatusBadge(cell.getValue()), minWidth: 130, widthGrow: 0, responsive: 0 },
      {
        title: "Folgen",
        field: "episode_a_id",
        sorter: "string",
        formatter(cell) {
          const row = cell.getRow().getData();
          return `${episodeAnchor(row.episode_a_id)} <span class="hint">vs</span> ${episodeAnchor(row.episode_b_id)}`;
        },
        minWidth: 170,
        widthGrow: 0,
        responsive: 1,
      },
      {
        title: "Stimmen",
        field: "votes_a",
        sorter: "number",
        formatter(cell) {
          const row = cell.getRow().getData();
          return `<div class="poll-stimmen-cell"><span>A ${formatInteger(row.votes_a)} : B ${formatInteger(row.votes_b)}</span>${voteSplitBar(row.votes_a, row.votes_b)}</div>`;
        },
        minWidth: 170,
        widthGrow: 4,
        responsive: 2,
      },
      {
        title: "Gesamt",
        field: "total_votes",
        sorter: "number",
        formatter(cell) {
          const row = cell.getRow().getData();
          return `<div class="poll-gesamt-cell"><span>${formatInteger(row.total_votes)}</span>${totalVotesBar(row.total_votes, maxVotes)}</div>`;
        },
        minWidth: 150,
        widthGrow: 0,
        responsive: 2,
      },
      {
        title: "Finalisiert",
        field: "finalized_at",
        sorter: "string",
        formatter(cell) {
          const row = cell.getRow().getData();
          return formatDate(row.finalized_at || row.closes_at);
        },
        minWidth: 132,
        widthGrow: 0,
        responsive: 3,
      },
    ],
  });
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
      ? `<img class="mini-cover" src="${escapeHtml(metaA.cover_url)}" alt="Cover Episode #${escapeHtml(poll.episode_a_id)}">`
      : `<div class="mini-cover mini-cover-fallback">#${escapeHtml(poll.episode_a_id)}</div>`;
    const coverB = metaB?.cover_url
      ? `<img class="mini-cover" src="${escapeHtml(metaB.cover_url)}" alt="Cover Episode #${escapeHtml(poll.episode_b_id)}">`
      : `<div class="mini-cover mini-cover-fallback">#${escapeHtml(poll.episode_b_id)}</div>`;
    const avgRank = poll.avg_pair_rank ? ` | Ø Rang ${formatMaybeNumber(poll.avg_pair_rank, 1)}` : "";

    row.innerHTML = `
      <div class="mini-pair-covers">${coverA}<span>VS</span>${coverB}</div>
      <div>
        <strong>${episodeAnchor(poll.episode_a_id)} vs ${episodeAnchor(poll.episode_b_id)}</strong>
        <p class="hint">A ${formatInteger(poll.votes_a)} : B ${formatInteger(poll.votes_b)} | Gesamt ${formatInteger(poll.total_votes)} | Margin ${formatInteger(poll.vote_margin)}${avgRank}</p>
        ${voteSplitBar(poll.votes_a, poll.votes_b)}
      </div>
    `;
    topExcitingList.appendChild(row);
  }
}

function renderTopPollChart(canvas, existingChart, polls, title) {
  if (existingChart) {
    existingChart.destroy();
  }

  if (!polls.length) {
    return null;
  }

  const labels = polls.map((poll) => `#${poll.episode_a_id} vs #${poll.episode_b_id}`);
  const datasetA = polls.map((poll) => poll.votes_a);
  const datasetB = polls.map((poll) => poll.votes_b);

  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Folge A",
          data: datasetA,
          backgroundColor: cssColorVar("--chart-primary-fill"),
          borderColor: cssColorVar("--chart-primary"),
          borderWidth: 1,
          borderRadius: 0,
          borderSkipped: false,
        },
        {
          label: "Folge B",
          data: datasetB,
          backgroundColor: cssColorVar("--chart-secondary-fill"),
          borderColor: cssColorVar("--chart-secondary"),
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
        tooltip: {
          callbacks: {
            title(items) {
              const poll = polls[items[0].dataIndex];
              return `${title}: #${poll.episode_a_id} vs #${poll.episode_b_id}`;
            },
            label(context) {
              const poll = polls[context.dataIndex];
              const rankInfo = poll.avg_pair_rank ? ` | Ø Rang ${formatMaybeNumber(poll.avg_pair_rank, 1)}` : "";
              return `A ${formatInteger(poll.votes_a)} : B ${formatInteger(poll.votes_b)} | Gesamt ${formatInteger(poll.total_votes)}${rankInfo}`;
            },
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          beginAtZero: true,
          title: {
            display: true,
            text: "Stimmen (A + B)",
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
  topReachChart = renderTopPollChart(topReachCanvas, topReachChart, reach, "Reichweite");
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

  votesTrendChart = new Chart(votesTrendCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Gesamtstimmen",
          data: votes,
          borderColor: cssColorVar("--chart-primary"),
          backgroundColor: cssColorVar("--chart-primary-fill"),
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.25,
        },
        {
          label: "7-Umfragen-Mittel",
          data: rollingAverage,
          borderColor: cssColorVar("--chart-secondary"),
          backgroundColor: cssColorVar("--chart-secondary-fill"),
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

function setEpisodeInChart(episodeId) {
  episodeSelect.value = String(episodeId);
  renderHistoryChart(String(episodeId));
  historySection.scrollIntoView({ behavior: "smooth", block: "start" });
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
      ? `<img class="engagement-hero" src="${escapeHtml(metadata.cover_url)}" alt="Cover Episode #${escapeHtml(card.episode_id)}">`
      : `<div class="engagement-hero engagement-cover-fallback">#${escapeHtml(card.episode_id)}</div>`;

    const item = document.createElement("article");
    item.className = "engagement-card";
    item.id = `episode-card-${card.episode_id}`;
    item.innerHTML = `
      ${cover}
      <div class="engagement-header">
        <div>
          <p class="engagement-rank">Rang ${escapeHtml(card.rank)}</p>
          <h3>${escapeHtml(getEpisodeLabel(card.episode_id))}</h3>
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

  historyChart = new Chart(historyCanvas, {
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
          borderColor: cssColorVar("--chart-primary"),
          backgroundColor: cssColorVar("--chart-primary"),
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 4,
          tension: 0.25,
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

function setActiveSectionLink(sectionId) {
  for (const link of sectionSwitcherLinks) {
    const isActive = link.dataset.target === sectionId;
    link.classList.toggle("is-active", isActive);
    if (isActive) {
      link.setAttribute("aria-current", "true");
    } else {
      link.removeAttribute("aria-current");
    }
  }
}

function initializeSectionSwitcher() {
  if (!sectionSwitcher) {
    return;
  }

  for (const link of sectionSwitcherLinks) {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const target = document.getElementById(link.dataset.target);
      if (!target) {
        return;
      }
      setActiveSectionLink(link.dataset.target);
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (sectionObserver) {
    sectionObserver.disconnect();
  }

  const sectionTargets = sectionSwitcherLinks
    .map((link) => document.getElementById(link.dataset.target))
    .filter(Boolean);

  sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible?.target?.id) {
      return;
    }
    setActiveSectionLink(visible.target.id);
  }, {
    root: null,
    rootMargin: "-35% 0px -55% 0px",
    threshold: [0.1, 0.25, 0.5],
  });

  for (const section of sectionTargets) {
    sectionObserver.observe(section);
  }
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
  initializeRankingTable();
  initializePollsTable();
  renderTopPollCharts();
  renderVotesTrendChart();
  renderEpisodeEngagementCards();
  renderEpisodeSelect();
  renderHistoryChart(String(pageData.episode_ids[0]));
  initializeSectionSwitcher();
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
  initializePollsTable();
  renderTopPollCharts();
  renderVotesTrendChart();
  initializeSectionSwitcher();
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
