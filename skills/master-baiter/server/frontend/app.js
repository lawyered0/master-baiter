/**
 * Master-Baiter Dashboard — Frontend Application
 * Real-time scam baiting session monitor with live WebSocket updates,
 * animated counters, toast notifications, and keyboard navigation.
 */

// ─── State ───────────────────────────────────────────────────────────────────
let currentView = 'sessions';
let currentSessionId = null;
let currentReportId = null;
let ws = null;
let wsRetryCount = 0;
let charts = {};
let liveCounterInterval = null;
let summarySnapshot = null;

// ─── API ─────────────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
    const res = await fetch(path, { ...opts });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// ─── WebSocket with exponential backoff ──────────────────────────────────────
function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/live`);

    ws.onopen = () => {
        wsRetryCount = 0;
        document.getElementById('ws-status').className = 'status-dot connected';
        document.getElementById('ws-label').textContent = 'Live';
    };

    ws.onclose = () => {
        document.getElementById('ws-status').className = 'status-dot disconnected';
        document.getElementById('ws-label').textContent = 'Reconnecting...';
        const delay = Math.min(1000 * 2 ** wsRetryCount++, 30000);
        setTimeout(connectWS, delay);
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleLiveUpdate(msg);
        } catch (e) {
            console.warn('Invalid WebSocket message:', e);
        }
    };
}

function handleLiveUpdate(msg) {
    // Flash the status dot
    const dot = document.getElementById('ws-status');
    dot.style.boxShadow = '0 0 8px 2px var(--green)';
    setTimeout(() => (dot.style.boxShadow = ''), 600);

    const { type, data } = msg;

    switch (type) {
        case 'session_update':
            if (currentView === 'sessions') loadSessions();
            if (currentView === 'analytics') loadAnalytics();
            if (currentSessionId === data.session_id) loadSessionDetail(currentSessionId);
            showToast(`Session ${data?.session_id?.slice(0, 8) || 'unknown'}… updated`, 'info');
            break;
        case 'evidence_update':
            if (currentSessionId === data.session_id) loadSessionDetail(currentSessionId);
            if (currentView === 'sessions') loadSessions();
            break;
        case 'intel_update':
            if (currentView === 'intel') loadIntel();
            showToast('New intel extracted', 'success');
            break;
        case 'gamification_update':
            if (data.event === 'achievement_unlocked') {
                showAchievementToast(data.achievement);
            }
            if (currentView === 'achievements') loadAchievements();
            updateNavLevel();
            break;
    }
}

// ─── Toast Notifications ─────────────────────────────────────────────────────
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText =
            'position:fixed;top:68px;right:24px;z-index:200;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
        document.body.appendChild(container);
    }

    const icons = { info: '🔔', success: '✅', warning: '⚠️', danger: '🚨' };
    const colors = { info: 'var(--accent)', success: 'var(--green)', warning: 'var(--orange)', danger: 'var(--red)' };

    const toast = document.createElement('div');
    toast.style.cssText = `
        background:var(--bg-card);border:1px solid ${colors[type]};border-radius:8px;padding:10px 16px;
        display:flex;align-items:center;gap:8px;font-size:13px;opacity:0;transform:translateX(40px);
        transition:all 0.3s ease;pointer-events:auto;box-shadow:0 4px 12px rgba(0,0,0,0.3);
    `;
    toast.innerHTML = `<span>${icons[type] || '🔔'}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── Navigation ──────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        switchView(link.dataset.view);
    });
});

function switchView(view) {
    if (currentView === 'analytics' && view !== 'analytics' && liveCounterInterval) {
        clearInterval(liveCounterInterval);
        liveCounterInterval = null;
    }
    currentView = view;
    document.querySelectorAll('.nav-link').forEach(l =>
        l.classList.toggle('active', l.dataset.view === view)
    );
    document.querySelectorAll('.view').forEach(v =>
        v.classList.toggle('active', v.id === `view-${view}`)
    );
    switch (view) {
        case 'sessions':     loadSessions(); break;
        case 'intel':        loadIntel(); break;
        case 'reports':      loadReports(); break;
        case 'analytics':    loadAnalytics(); break;
        case 'achievements': loadAchievements(); break;
    }
}

// ─── Formatters ──────────────────────────────────────────────────────────────
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0s';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function formatTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const diffMs = Date.now() - d;
    if (diffMs < 60000) return 'just now';
    if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
    if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`;
    return d.toLocaleDateString();
}

const CHANNEL_EMOJI = {
    whatsapp: '💬', telegram: '✈️', discord: '🎮', signal: '🔒',
    email: '📧', slack: '💼', sms: '📱', irc: '🖥️', teams: '👥', matrix: '🟢',
};

function channelIcon(ch) {
    return `<span class="channel-icon">${CHANNEL_EMOJI[ch] || '📨'} ${ch}</span>`;
}

function severityBadge(sev) {
    const labels = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical', 5: 'Emergency' };
    return `<span class="severity-badge severity-${sev}">${sev} — ${labels[sev] || '?'}</span>`;
}

function statusBadge(status) {
    return `<span class="status-badge status-${status}">${status}</span>`;
}

function scamLabel(type) {
    if (!type) return '—';
    return type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function emptyState(icon, msg) {
    return `<tr><td colspan="99"><div class="empty-state"><div class="icon">${icon}</div><div class="message">${msg}</div></div></td></tr>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Sessions View ───────────────────────────────────────────────────────────
async function loadSessions() {
    const status  = document.getElementById('filter-status').value;
    const channel = document.getElementById('filter-channel').value;
    const severity = document.getElementById('filter-severity').value;

    let qs = '?limit=50';
    if (status) qs += `&status=${status}`;
    if (channel) qs += `&channel=${channel}`;
    if (severity) qs += `&severity_min=${severity}&severity_max=${severity}`;

    const data = await api(`/api/sessions${qs}`);
    const tbody = document.getElementById('sessions-body');

    if (!data.sessions?.length) {
        tbody.innerHTML = emptyState('🎣', 'No sessions yet. Waiting for scammers to bite…');
        return;
    }

    tbody.innerHTML = data.sessions.map(s => `
        <tr onclick="openSession('${escapeHtml(s.id)}')"
            class="${s.severity >= 4 ? 'row-pulse' : ''}"
            data-severity="${s.severity}">
            <td>${channelIcon(s.channel)}</td>
            <td>${scamLabel(s.scam_type)}</td>
            <td>${s.severity ? severityBadge(s.severity) : '—'}</td>
            <td>${s.persona || '—'}</td>
            <td>${statusBadge(s.status)}</td>
            <td><span class="msg-count">${s.message_count}</span></td>
            <td class="time-wasted-cell">${formatDuration(s.time_wasted_seconds)}</td>
            <td>${formatTime(s.updated_at)}</td>
        </tr>
    `).join('');
}

['filter-status', 'filter-channel', 'filter-severity'].forEach(id => {
    document.getElementById(id).addEventListener('change', loadSessions);
});

// ─── Session Detail ──────────────────────────────────────────────────────────
async function openSession(id) {
    currentSessionId = id;
    document.getElementById('session-detail').classList.remove('hidden');
    await loadSessionDetail(id);
}

async function loadSessionDetail(id) {
    const [session, transcript] = await Promise.all([
        api(`/api/sessions/${id}`),
        api(`/api/sessions/${id}/transcript?limit=200`),
    ]);

    document.getElementById('detail-title').textContent =
        `${CHANNEL_EMOJI[session.channel] || '📨'} ${scamLabel(session.scam_type)} — ${session.persona || 'No persona'}`;

    document.getElementById('detail-info').innerHTML = `
        <div><strong>Session:</strong> ${escapeHtml(id.slice(0, 12))}…</div>
        <div><strong>Channel:</strong> ${escapeHtml(session.channel)}</div>
        <div><strong>Sender:</strong> ${escapeHtml(session.sender_id)}</div>
        <div><strong>Scam Type:</strong> ${scamLabel(session.scam_type)}</div>
        <div><strong>Severity:</strong> ${session.severity ? severityBadge(session.severity) : '—'}</div>
        <div><strong>Mode:</strong> ${session.mode === 'passive' ? '👁️ Passive' : '🎣 Active Bait'}</div>
        <div><strong>Messages:</strong> ${session.message_count}</div>
        <div><strong>Time Wasted:</strong> <span class="time-pulse">${formatDuration(session.time_wasted_seconds)}</span></div>
        <div><strong>Status:</strong> ${statusBadge(session.status)}</div>
    `;

    // Transcript — chat bubble view
    const feed = document.getElementById('transcript-feed');
    if (transcript.entries?.length) {
        feed.innerHTML = transcript.entries.map(e => `
            <div class="msg msg-${e.direction}" style="animation: fadeSlideIn 0.3s ease">
                <div class="msg-content">${escapeHtml(e.content)}</div>
                <div class="msg-meta">
                    ${e.direction === 'inbound' ? '🐟 Scammer' : '🎣 Bait'} · ${formatTime(e.timestamp)}
                </div>
            </div>
        `).join('');
        feed.scrollTop = feed.scrollHeight;
    } else {
        feed.innerHTML = '<div class="empty-state"><div class="icon">📭</div><div class="message">No messages yet</div></div>';
    }

    // Extracted intel
    const intelList = document.getElementById('detail-intel-list');
    if (session.intel?.length) {
        intelList.innerHTML = session.intel.map(i =>
            `<span class="intel-chip" title="${i.platform || ''}">${i.type}: <strong>${escapeHtml(i.value)}</strong></span>`
        ).join('');
    } else {
        intelList.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No intel extracted yet</span>';
    }
}

function closeDetail() {
    document.getElementById('session-detail').classList.add('hidden');
    currentSessionId = null;
}

async function escalateSession() {
    if (!currentSessionId) return;
    const sev = prompt('Set severity level (1-5):', '4');
    if (!sev || isNaN(sev) || sev < 1 || sev > 5) return;
    await api(`/api/sessions/${currentSessionId}/escalate?severity=${sev}`, { method: 'POST' });
    showToast('Session escalated to severity ' + sev, 'warning');
    await loadSessionDetail(currentSessionId);
    loadSessions();
}

async function closeSession() {
    if (!currentSessionId) return;
    if (!confirm('Close this session? The scammer will no longer receive responses.')) return;
    await api(`/api/sessions/${currentSessionId}/close`, { method: 'POST' });
    showToast('Session closed', 'info');
    closeDetail();
    loadSessions();
}

// ─── Intel View ──────────────────────────────────────────────────────────────
let intelSearchTimeout;

async function loadIntel() {
    const type = document.getElementById('intel-type-filter').value;
    const search = document.getElementById('intel-search').value;

    let data;
    if (search) {
        data = await api(`/api/intel/search?q=${encodeURIComponent(search)}`);
        data = { items: data.results || [] };
    } else {
        let qs = '?limit=50';
        if (type) qs += `&type=${type}`;
        data = await api(`/api/intel${qs}`);
    }

    const tbody = document.getElementById('intel-body');
    if (!data.items?.length) {
        tbody.innerHTML = emptyState('🔍', search ? `No results for "${escapeHtml(search)}"` : 'No intel collected yet');
        return;
    }

    tbody.innerHTML = data.items.map(i => `
        <tr onclick="viewIntelNetwork('${escapeHtml(i.value)}')" style="cursor:pointer">
            <td><span class="intel-type-badge type-${i.type}">${i.type}</span></td>
            <td class="mono"><strong>${escapeHtml(i.value)}</strong></td>
            <td>${i.platform || '—'}</td>
            <td>${i.session_count != null ? `<span class="session-count">${i.session_count}</span>` : (i.session_id ? i.session_id.slice(0, 8) + '…' : '—')}</td>
            <td>${formatTime(i.first_seen)}</td>
            <td>${formatTime(i.last_seen)}</td>
        </tr>
    `).join('');
}

async function viewIntelNetwork(value) {
    const data = await api(`/api/intel/network/${encodeURIComponent(value)}`);
    showToast(`${data.session_count} linked session${data.session_count !== 1 ? 's' : ''} for "${value}"`, 'info');
    // TODO: render force-directed graph in a modal
}

document.getElementById('intel-type-filter').addEventListener('change', loadIntel);
document.getElementById('intel-search').addEventListener('input', () => {
    clearTimeout(intelSearchTimeout);
    intelSearchTimeout = setTimeout(loadIntel, 300);
});

// ─── Reports View ────────────────────────────────────────────────────────────
async function loadReports() {
    const type = document.getElementById('report-type-filter').value;
    const status = document.getElementById('report-status-filter').value;

    let qs = '?limit=50';
    if (type) qs += `&report_type=${type}`;
    if (status) qs += `&status=${status}`;

    const data = await api(`/api/reports${qs}`);
    const tbody = document.getElementById('reports-body');

    if (!data.reports?.length) {
        tbody.innerHTML = emptyState('📋', 'No reports generated yet');
        return;
    }

    const typeIcons = { ic3: '🏛️', ftc: '🛡️', ncmec: '🚨', local_pd: '👮', platform_abuse: '📢' };

    tbody.innerHTML = data.reports.map(r => `
        <tr onclick="openReport('${escapeHtml(String(r.id))}')">
            <td>${typeIcons[r.report_type] || '📄'} ${escapeHtml(r.report_type).toUpperCase()}</td>
            <td>${escapeHtml(r.session_id.slice(0, 12))}…</td>
            <td>${statusBadge(r.status)}</td>
            <td>${formatTime(r.generated_at)}</td>
            <td>${r.submitted_at ? formatTime(r.submitted_at) : '—'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openReport('${escapeHtml(String(r.id))}')">View</button>
            </td>
        </tr>
    `).join('');
}

document.getElementById('report-type-filter').addEventListener('change', loadReports);
document.getElementById('report-status-filter').addEventListener('change', loadReports);

async function openReport(id) {
    currentReportId = id;
    const data = await api(`/api/reports/${id}`);

    document.getElementById('report-detail-title').textContent =
        `${data.report_type.toUpperCase()} Report — Session ${data.session_id.slice(0, 12)}…`;
    document.getElementById('report-content').textContent = data.content || '(No content)';

    document.getElementById('btn-mark-reviewed').style.display = data.status === 'draft' ? '' : 'none';
    document.getElementById('btn-mark-submitted').style.display = data.status === 'reviewed' ? '' : 'none';

    document.getElementById('report-detail').classList.remove('hidden');
}

function closeReportDetail() {
    document.getElementById('report-detail').classList.add('hidden');
    currentReportId = null;
}

async function markReportReviewed() {
    if (!currentReportId) return;
    await api(`/api/reports/${currentReportId}/mark-reviewed`, { method: 'POST' });
    showToast('Report marked as reviewed ✓', 'success');
    await openReport(currentReportId);
    loadReports();
}

async function markReportSubmitted() {
    if (!currentReportId) return;
    if (!confirm('Confirm this report has been submitted to the appropriate authority?')) return;
    await api(`/api/reports/${currentReportId}/mark-submitted`, { method: 'POST' });
    showToast('Report marked as submitted ✓', 'success');
    await openReport(currentReportId);
    loadReports();
}

// ─── Analytics View ──────────────────────────────────────────────────────────
async function loadAnalytics() {
    const [summary, scamTypes, trends, effectiveness, channels] = await Promise.all([
        api('/api/analytics/summary'),
        api('/api/analytics/scam-types'),
        api('/api/analytics/trends'),
        api('/api/analytics/effectiveness'),
        api('/api/analytics/channels'),
    ]);

    summarySnapshot = summary;
    renderSummaryCards(summary);
    renderTrendsChart(trends);
    renderScamTypesChart(scamTypes);
    renderTimeWastedChart(scamTypes);
    renderChannelsChart(channels);
    renderEffectiveness(effectiveness);
    startLiveCounters();
}

function renderSummaryCards(s) {
    document.getElementById('summary-cards').innerHTML = `
        <div class="summary-card">
            <div class="label">Total Sessions</div>
            <div class="value accent" id="live-total">${s.total_sessions}</div>
        </div>
        <div class="summary-card">
            <div class="label">Active Now</div>
            <div class="value green" id="live-active">${s.active_sessions}</div>
        </div>
        <div class="summary-card">
            <div class="label">🕐 Time Wasted</div>
            <div class="value orange" id="live-time">${formatDuration(s.total_time_wasted_seconds)}</div>
        </div>
        <div class="summary-card">
            <div class="label">Messages Exchanged</div>
            <div class="value">${(s.total_messages || 0).toLocaleString()}</div>
        </div>
        <div class="summary-card">
            <div class="label">🔍 Intel Collected</div>
            <div class="value accent">${s.total_intel_items}</div>
        </div>
        <div class="summary-card">
            <div class="label">Reports Generated</div>
            <div class="value">${s.total_reports}</div>
        </div>
        <div class="summary-card">
            <div class="label">✅ Reports Submitted</div>
            <div class="value green">${s.reports_submitted}</div>
        </div>
    `;
}

function startLiveCounters() {
    if (liveCounterInterval) clearInterval(liveCounterInterval);
    if (!summarySnapshot) return;

    let currentSec = summarySnapshot.total_time_wasted_seconds || 0;
    const active = summarySnapshot.active_sessions || 0;

    liveCounterInterval = setInterval(() => {
        if (currentView !== 'analytics' || active === 0) return;
        currentSec += active; // each active session wastes 1s per second
        const el = document.getElementById('live-time');
        if (el) el.textContent = formatDuration(currentSec);
    }, 1000);
}

function renderTrendsChart(data) {
    renderChart('chart-trends', 'line', {
        labels: data.daily?.map(d => d.date) || [],
        datasets: [
            {
                label: 'Sessions',
                data: data.daily?.map(d => d.sessions) || [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.1)',
                fill: true, tension: 0.4,
            },
            {
                label: 'Messages',
                data: data.daily?.map(d => d.messages) || [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.1)',
                fill: true, tension: 0.4,
                yAxisID: 'y1',
            },
        ],
    }, {
        scales: {
            x:  { ticks: { color: '#6b7280' }, grid: { color: '#1f2937' } },
            y:  { ticks: { color: '#6b7280' }, grid: { color: '#1f2937' }, beginAtZero: true },
            y1: { position: 'right', ticks: { color: '#6b7280' }, grid: { display: false }, beginAtZero: true },
        },
    });
}

function renderScamTypesChart(data) {
    const colors = ['#3b82f6','#10b981','#f59e0b','#ef4444','#a855f7','#f97316','#06b6d4','#ec4899'];
    renderChart('chart-scam-types', 'doughnut', {
        labels: data.types?.map(t => scamLabel(t.scam_type)) || [],
        datasets: [{
            data: data.types?.map(t => t.count) || [],
            backgroundColor: colors, borderColor: '#111827', borderWidth: 2,
        }],
    });
}

function renderTimeWastedChart(data) {
    renderChart('chart-time-wasted', 'bar', {
        labels: data.types?.map(t => scamLabel(t.scam_type)) || [],
        datasets: [{
            label: 'Hours Wasted',
            data: data.types?.map(t => +(t.total_time_seconds / 3600).toFixed(1)) || [],
            backgroundColor: 'rgba(249,115,22,0.6)', borderColor: '#f97316', borderWidth: 1,
        }],
    }, { indexAxis: 'y' });
}

function renderChannelsChart(data) {
    const colors = ['#3b82f6','#10b981','#a855f7','#f59e0b','#ef4444','#06b6d4','#ec4899'];
    renderChart('chart-channels', 'polarArea', {
        labels: data.channels?.map(c => c.channel) || [],
        datasets: [{
            data: data.channels?.map(c => c.count) || [],
            backgroundColor: colors.map(c => c + '80'), borderColor: colors, borderWidth: 1,
        }],
    }, { scales: { r: { grid: { color: '#1f2937' }, ticks: { display: false } } } });
}

function renderChart(canvasId, type, data, extraOpts = {}) {
    if (charts[canvasId]) charts[canvasId].destroy();
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    const isDoughnutLike = type === 'doughnut' || type === 'polarArea';
    charts[canvasId] = new Chart(ctx, {
        type, data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: { color: '#9ca3af', font: { size: 11 } },
                    position: isDoughnutLike ? 'right' : 'top',
                },
            },
            scales: isDoughnutLike ? (extraOpts.scales || {}) : {
                x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' }, beginAtZero: true },
            },
            ...extraOpts,
        },
    });
}

function renderEffectiveness(data) {
    document.getElementById('effectiveness-metrics').innerHTML = `
        <div class="metric">
            <div class="label">Avg Session Duration</div>
            <div class="value">${data.avg_session_duration_minutes}m</div>
        </div>
        <div class="metric">
            <div class="label">Avg Messages / Session</div>
            <div class="value">${data.avg_messages_per_session}</div>
        </div>
        <div class="metric">
            <div class="label">Intel Extraction Rate</div>
            <div class="value">${data.intel_extraction_rate}%</div>
        </div>
        <div class="metric">
            <div class="label">Report Generation Rate</div>
            <div class="value">${data.report_generation_rate}%</div>
        </div>
    `;

    const tbody = document.getElementById('top-scammers-body');
    const items = data.top_scammer_identifiers || [];
    if (items.length) {
        tbody.innerHTML = items.map(s => `
            <tr onclick="viewIntelNetwork('${escapeHtml(s.value)}')" style="cursor:pointer">
                <td><span class="intel-type-badge type-${s.type}">${s.type}</span></td>
                <td class="mono">${escapeHtml(s.value)}</td>
                <td>${s.session_count}</td>
            </tr>
        `).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--text-dim)">No repeat offenders yet</td></tr>';
    }
}

// ─── Keyboard Shortcuts ──────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
    // Don't intercept if typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

    if (e.key === 'Escape') { closeDetail(); closeReportDetail(); }
    if (e.key === '1') switchView('sessions');
    if (e.key === '2') switchView('intel');
    if (e.key === '3') switchView('reports');
    if (e.key === '4') switchView('analytics');
    if (e.key === '5') switchView('achievements');
    if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        switch (currentView) {
            case 'sessions':     loadSessions(); break;
            case 'intel':        loadIntel(); break;
            case 'reports':      loadReports(); break;
            case 'analytics':    loadAnalytics(); break;
            case 'achievements': loadAchievements(); break;
        }
        showToast('Refreshed', 'info');
    }
});

// ─── Achievements View ──────────────────────────────────────────────────────
let currentAchCategory = '';

async function loadAchievements() {
    const [profile, stats, achievements] = await Promise.all([
        api('/api/gamification/profile'),
        api('/api/gamification/stats'),
        api(`/api/gamification/achievements${currentAchCategory ? `?category=${currentAchCategory}` : ''}`),
    ]);

    renderProfileBanner(profile);
    renderFunStats(stats);
    renderAchievementGrid(achievements.achievements || []);
}

function renderProfileBanner(p) {
    document.getElementById('profile-level-num').textContent = p.level;
    document.getElementById('profile-level-title').textContent = p.title;

    const bar = document.getElementById('xp-progress-bar');
    bar.style.width = `${Math.min(p.progress_percent, 100)}%`;

    document.getElementById('xp-progress-label').textContent =
        `${p.total_xp.toLocaleString()} / ${p.xp_for_next_level.toLocaleString()} XP`;

    document.getElementById('profile-achievements-count').textContent =
        `${p.achievements_unlocked} / ${p.achievements_total} Achievements`;
    document.getElementById('profile-streak').textContent = `Streak: ${p.current_streak}`;
    document.getElementById('profile-total-xp').textContent = `Total XP: ${p.total_xp.toLocaleString()}`;

    // Update nav badge too
    const badge = document.getElementById('nav-level');
    if (badge) {
        badge.textContent = `Lv.${p.level}`;
        badge.title = p.title;
    }
}

function renderFunStats(s) {
    const cards = document.getElementById('fun-stats-cards');
    cards.innerHTML = `
        <div class="summary-card">
            <div class="label">Scammer Time Wasted</div>
            <div class="value orange">${s.total_time_wasted_human}</div>
        </div>
        <div class="summary-card">
            <div class="label">Scammer Salary Burned</div>
            <div class="value green">${s.scammer_salary_wasted}</div>
        </div>
        <div class="summary-card">
            <div class="label">Intel Extracted</div>
            <div class="value accent">${s.intel_collected}</div>
        </div>
        <div class="summary-card">
            <div class="label">Reports Filed</div>
            <div class="value">${s.reports_filed}</div>
        </div>
        <div class="summary-card">
            <div class="label">Longest Session</div>
            <div class="value">${s.longest_session_human}</div>
        </div>
        <div class="summary-card">
            <div class="label">Fun Fact</div>
            <div class="value fun-fact">${s.fun_fact}</div>
        </div>
    `;
}

function renderAchievementGrid(achievements) {
    const grid = document.getElementById('achievement-grid');

    if (!achievements.length) {
        grid.innerHTML = '<div class="empty-state"><div class="icon">🏆</div><div class="message">No achievements in this category</div></div>';
        return;
    }

    grid.innerHTML = achievements.map(a => `
        <div class="achievement-card ${a.unlocked ? 'unlocked' : 'locked'}">
            <div class="ach-icon">${a.icon}</div>
            <div class="ach-info">
                <div class="ach-name">${escapeHtml(a.name)}</div>
                <div class="ach-desc">${escapeHtml(a.description)}</div>
            </div>
            <div class="ach-xp">+${a.xp_reward} XP</div>
            ${a.unlocked ? `<div class="ach-unlocked-date">${formatTime(a.unlocked_at)}</div>` : ''}
        </div>
    `).join('');
}

function showAchievementToast(achievement) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText =
            'position:fixed;top:68px;right:24px;z-index:200;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'achievement-toast';
    toast.style.cssText = `
        background:var(--bg-card);border:2px solid var(--gold);border-radius:8px;padding:12px 18px;
        display:flex;align-items:center;gap:10px;font-size:14px;opacity:0;transform:translateX(40px) scale(0.9);
        transition:all 0.4s cubic-bezier(0.34,1.56,0.64,1);pointer-events:auto;
        box-shadow:0 4px 20px rgba(251,191,36,0.3);
    `;
    toast.innerHTML = `
        <span style="font-size:24px">${achievement.icon || '🏆'}</span>
        <div>
            <div style="color:var(--gold);font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.05em">Achievement Unlocked</div>
            <div style="font-weight:600">${escapeHtml(achievement.name)}</div>
        </div>
        <span class="ach-xp-toast">+${achievement.xp_reward} XP</span>
    `;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0) scale(1)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px) scale(0.9)';
        setTimeout(() => toast.remove(), 400);
    }, 6000);
}

async function updateNavLevel() {
    try {
        const profile = await api('/api/gamification/profile');
        const badge = document.getElementById('nav-level');
        if (badge) {
            badge.textContent = `Lv.${profile.level}`;
            badge.title = profile.title;
        }
    } catch (e) { /* ignore */ }
}

// Achievement category tab clicks
document.querySelectorAll('.ach-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.ach-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentAchCategory = tab.dataset.category;
        loadAchievements();
    });
});

// ─── Init ────────────────────────────────────────────────────────────────────
connectWS();
loadSessions();
updateNavLevel();
