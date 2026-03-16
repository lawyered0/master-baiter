/* Master-Baiter Dashboard — Frontend Application */

const API = '';
let ws = null;
let currentSessionId = null;
let currentReportId = null;
let charts = {};

// ─── Navigation ───────────────────────────────────────────────
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const view = link.dataset.view;
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        link.classList.add('active');
        document.getElementById(`view-${view}`).classList.add('active');
        loadView(view);
    });
});

function loadView(view) {
    switch (view) {
        case 'sessions': loadSessions(); break;
        case 'intel': loadIntel(); break;
        case 'reports': loadReports(); break;
        case 'analytics': loadAnalytics(); break;
    }
}

// ─── WebSocket ────────────────────────────────────────────────
function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/live`);

    ws.onopen = () => {
        document.getElementById('ws-status').className = 'status-dot connected';
        document.getElementById('ws-label').textContent = 'Live';
    };

    ws.onclose = () => {
        document.getElementById('ws-status').className = 'status-dot disconnected';
        document.getElementById('ws-label').textContent = 'Disconnected';
        setTimeout(connectWS, 3000);
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleLiveUpdate(msg);
    };
}

function handleLiveUpdate(msg) {
    const activeView = document.querySelector('.view.active')?.id;
    switch (msg.type) {
        case 'session_update':
            if (activeView === 'view-sessions') loadSessions();
            if (currentSessionId === msg.data.session_id) loadSessionDetail(currentSessionId);
            break;
        case 'evidence_update':
            if (currentSessionId === msg.data.session_id) loadSessionDetail(currentSessionId);
            break;
        case 'intel_update':
            if (activeView === 'view-intel') loadIntel();
            break;
    }
}

// ─── API Helpers ──────────────────────────────────────────────
async function api(path, opts = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...opts,
    });
    return res.json();
}

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0s';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
}

function formatTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now - d;
    if (diffMs < 60000) return 'Just now';
    if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
    if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`;
    return d.toLocaleDateString();
}

function severityBadge(sev) {
    const labels = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical', 5: 'Emergency' };
    return `<span class="severity-badge severity-${sev}">${sev} - ${labels[sev] || '?'}</span>`;
}

function statusBadge(status) {
    return `<span class="status-badge status-${status}">${status}</span>`;
}

const channelEmoji = {
    whatsapp: '📱', telegram: '✈️', discord: '🎮', signal: '🔒',
    email: '📧', slack: '💬', irc: '💻', sms: '📲', teams: '👥',
};

function channelIcon(ch) {
    return `<span class="channel-icon">${channelEmoji[ch] || '💬'} ${ch}</span>`;
}

function emptyState(icon, message) {
    return `<tr><td colspan="99"><div class="empty-state"><div class="icon">${icon}</div><div class="message">${message}</div></div></td></tr>`;
}

// ─── Sessions ─────────────────────────────────────────────────
async function loadSessions() {
    const status = document.getElementById('filter-status').value;
    const channel = document.getElementById('filter-channel').value;
    const severity = document.getElementById('filter-severity').value;

    let qs = '?limit=50';
    if (status) qs += `&status=${status}`;
    if (channel) qs += `&channel=${channel}`;
    if (severity) qs += `&severity_min=${severity}&severity_max=${severity}`;

    const data = await api(`/api/sessions${qs}`);
    const tbody = document.getElementById('sessions-body');

    if (!data.sessions?.length) {
        tbody.innerHTML = emptyState('🎣', 'No sessions yet. Waiting for scammers to bite...');
        return;
    }

    tbody.innerHTML = data.sessions.map(s => `
        <tr onclick="openSession('${s.id}')">
            <td>${channelIcon(s.channel)}</td>
            <td>${s.scam_type || '—'}</td>
            <td>${s.severity ? severityBadge(s.severity) : '—'}</td>
            <td>${s.persona || '—'}</td>
            <td>${statusBadge(s.status)}</td>
            <td>${s.message_count}</td>
            <td>${formatDuration(s.time_wasted_seconds)}</td>
            <td>${formatTime(s.updated_at)}</td>
        </tr>
    `).join('');
}

// Session filters
['filter-status', 'filter-channel', 'filter-severity'].forEach(id => {
    document.getElementById(id).addEventListener('change', loadSessions);
});

async function openSession(id) {
    currentSessionId = id;
    document.getElementById('session-detail').classList.remove('hidden');
    await loadSessionDetail(id);
}

function closeDetail() {
    document.getElementById('session-detail').classList.add('hidden');
    currentSessionId = null;
}

async function loadSessionDetail(id) {
    const [session, transcript] = await Promise.all([
        api(`/api/sessions/${id}`),
        api(`/api/sessions/${id}/transcript?limit=200`),
    ]);

    document.getElementById('detail-title').textContent =
        `${channelEmoji[session.channel] || '💬'} ${session.scam_type || 'Unknown'} — ${session.persona || 'No persona'}`;

    document.getElementById('detail-info').innerHTML = `
        <strong>Session:</strong> ${id.slice(0, 8)}...<br>
        <strong>Channel:</strong> ${session.channel}<br>
        <strong>Sender:</strong> ${session.sender_id}<br>
        <strong>Type:</strong> ${session.scam_type || '—'}<br>
        <strong>Severity:</strong> ${session.severity ? severityBadge(session.severity) : '—'}<br>
        <strong>Mode:</strong> ${session.mode}<br>
        <strong>Messages:</strong> ${session.message_count}<br>
        <strong>Time Wasted:</strong> ${formatDuration(session.time_wasted_seconds)}<br>
        <strong>Status:</strong> ${statusBadge(session.status)}
    `;

    const feed = document.getElementById('transcript-feed');
    if (transcript.entries?.length) {
        feed.innerHTML = transcript.entries.map(e => `
            <div class="msg msg-${e.direction}">
                <div>${escapeHtml(e.content)}</div>
                <div class="msg-meta">${e.direction === 'inbound' ? '🔴 Scammer' : '🎣 Bot'} · ${formatTime(e.timestamp)}</div>
            </div>
        `).join('');
        feed.scrollTop = feed.scrollHeight;
    } else {
        feed.innerHTML = '<div class="empty-state"><div class="icon">📭</div><div class="message">No messages yet</div></div>';
    }

    const intelList = document.getElementById('detail-intel-list');
    if (session.intel?.length) {
        intelList.innerHTML = session.intel.map(i =>
            `<span class="intel-chip" title="${i.platform}">${i.type}: ${i.value}</span>`
        ).join('');
    } else {
        intelList.innerHTML = '<span style="color:var(--text-dim);font-size:12px">No intel extracted yet</span>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function escalateSession() {
    if (!currentSessionId) return;
    const sev = prompt('Set severity level (1-5):');
    if (!sev || isNaN(sev) || sev < 1 || sev > 5) return;
    await api(`/api/sessions/${currentSessionId}/escalate?severity=${sev}`, { method: 'POST' });
    await loadSessionDetail(currentSessionId);
    loadSessions();
}

async function closeSession() {
    if (!currentSessionId) return;
    if (!confirm('Close this session? The scammer will no longer receive responses.')) return;
    await api(`/api/sessions/${currentSessionId}/close`, { method: 'POST' });
    await loadSessionDetail(currentSessionId);
    loadSessions();
}

// ─── Intel ────────────────────────────────────────────────────
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
        tbody.innerHTML = emptyState('🔍', 'No intel collected yet');
        return;
    }

    tbody.innerHTML = data.items.map(i => `
        <tr>
            <td><span class="intel-chip">${i.type}</span></td>
            <td><strong>${escapeHtml(i.value)}</strong></td>
            <td>${i.platform || '—'}</td>
            <td>${i.session_count ?? '—'}</td>
            <td>${formatTime(i.first_seen)}</td>
            <td>${formatTime(i.last_seen)}</td>
        </tr>
    `).join('');
}

document.getElementById('intel-type-filter').addEventListener('change', loadIntel);
let intelSearchTimeout;
document.getElementById('intel-search').addEventListener('input', () => {
    clearTimeout(intelSearchTimeout);
    intelSearchTimeout = setTimeout(loadIntel, 300);
});

// ─── Reports ──────────────────────────────────────────────────
async function loadReports() {
    const type = document.getElementById('report-type-filter').value;
    const status = document.getElementById('report-status-filter').value;

    let qs = '?limit=50';
    if (type) qs += `&report_type=${type}`;
    if (status) qs += `&status=${status}`;

    const data = await api(`/api/reports${qs}`);
    const tbody = document.getElementById('reports-body');

    if (!data.reports?.length) {
        tbody.innerHTML = emptyState('📄', 'No reports generated yet');
        return;
    }

    tbody.innerHTML = data.reports.map(r => `
        <tr onclick="openReport(${r.id})">
            <td><span class="intel-chip">${r.report_type.toUpperCase()}</span></td>
            <td>${r.session_id.slice(0, 8)}...</td>
            <td>${statusBadge(r.status)}</td>
            <td>${formatTime(r.generated_at)}</td>
            <td>${r.submitted_at ? formatTime(r.submitted_at) : '—'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openReport(${r.id})">View</button>
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
        `${data.report_type.toUpperCase()} Report — Session ${data.session_id.slice(0, 8)}...`;
    document.getElementById('report-content').textContent = data.content || '(No content)';

    document.getElementById('btn-mark-reviewed').style.display =
        data.status === 'draft' ? '' : 'none';
    document.getElementById('btn-mark-submitted').style.display =
        data.status === 'reviewed' ? '' : 'none';

    document.getElementById('report-detail').classList.remove('hidden');
}

function closeReportDetail() {
    document.getElementById('report-detail').classList.add('hidden');
    currentReportId = null;
}

async function markReportReviewed() {
    if (!currentReportId) return;
    await api(`/api/reports/${currentReportId}/mark-reviewed`, { method: 'POST' });
    await openReport(currentReportId);
    loadReports();
}

async function markReportSubmitted() {
    if (!currentReportId) return;
    if (!confirm('Mark this report as submitted? This indicates it has been filed with the relevant agency.')) return;
    await api(`/api/reports/${currentReportId}/mark-submitted`, { method: 'POST' });
    await openReport(currentReportId);
    loadReports();
}

// ─── Analytics ────────────────────────────────────────────────
async function loadAnalytics() {
    const [summary, scamTypes, trends, effectiveness, channels] = await Promise.all([
        api('/api/analytics/summary'),
        api('/api/analytics/scam-types'),
        api('/api/analytics/trends'),
        api('/api/analytics/effectiveness'),
        api('/api/analytics/channels'),
    ]);

    // Summary cards
    document.getElementById('summary-cards').innerHTML = `
        <div class="summary-card">
            <div class="label">Total Sessions</div>
            <div class="value accent">${summary.total_sessions}</div>
        </div>
        <div class="summary-card">
            <div class="label">Active Now</div>
            <div class="value green">${summary.active_sessions}</div>
        </div>
        <div class="summary-card">
            <div class="label">Time Wasted</div>
            <div class="value orange">${summary.total_time_wasted_hours}h</div>
        </div>
        <div class="summary-card">
            <div class="label">Messages Sent</div>
            <div class="value">${summary.total_messages}</div>
        </div>
        <div class="summary-card">
            <div class="label">Intel Collected</div>
            <div class="value accent">${summary.total_intel_items}</div>
        </div>
        <div class="summary-card">
            <div class="label">Reports Generated</div>
            <div class="value">${summary.total_reports}</div>
        </div>
        <div class="summary-card">
            <div class="label">Reports Submitted</div>
            <div class="value green">${summary.reports_submitted}</div>
        </div>
    `;

    // Trends chart
    renderChart('chart-trends', 'line', {
        labels: trends.daily?.map(d => d.date) || [],
        datasets: [
            {
                label: 'Sessions',
                data: trends.daily?.map(d => d.sessions) || [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.1)',
                fill: true,
                tension: 0.3,
            },
            {
                label: 'Messages',
                data: trends.daily?.map(d => d.messages) || [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.1)',
                fill: true,
                tension: 0.3,
            },
        ],
    });

    // Scam types chart
    const typeColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#f97316', '#06b6d4', '#ec4899'];
    renderChart('chart-scam-types', 'doughnut', {
        labels: scamTypes.types?.map(t => t.scam_type) || [],
        datasets: [{
            data: scamTypes.types?.map(t => t.count) || [],
            backgroundColor: typeColors,
        }],
    });

    // Time wasted chart
    renderChart('chart-time-wasted', 'bar', {
        labels: scamTypes.types?.map(t => t.scam_type) || [],
        datasets: [{
            label: 'Hours Wasted',
            data: scamTypes.types?.map(t => Math.round(t.total_time_seconds / 3600 * 10) / 10) || [],
            backgroundColor: '#f59e0b',
        }],
    });

    // Channels chart
    renderChart('chart-channels', 'doughnut', {
        labels: channels.channels?.map(c => c.channel) || [],
        datasets: [{
            data: channels.channels?.map(c => c.count) || [],
            backgroundColor: typeColors,
        }],
    });

    // Effectiveness
    document.getElementById('effectiveness-metrics').innerHTML = `
        <div class="metric">
            <div class="label">Avg Session Duration</div>
            <div class="value">${effectiveness.avg_session_duration_minutes}m</div>
        </div>
        <div class="metric">
            <div class="label">Avg Messages / Session</div>
            <div class="value">${effectiveness.avg_messages_per_session}</div>
        </div>
        <div class="metric">
            <div class="label">Intel Extraction Rate</div>
            <div class="value">${effectiveness.intel_extraction_rate}%</div>
        </div>
        <div class="metric">
            <div class="label">Report Generation Rate</div>
            <div class="value">${effectiveness.report_generation_rate}%</div>
        </div>
    `;

    document.getElementById('top-scammers-body').innerHTML =
        (effectiveness.top_scammer_identifiers || []).map(s => `
            <tr>
                <td><span class="intel-chip">${s.type}</span></td>
                <td>${escapeHtml(s.value)}</td>
                <td>${s.session_count}</td>
            </tr>
        `).join('') || '<tr><td colspan="3" style="text-align:center;color:var(--text-dim)">No data yet</td></tr>';
}

function renderChart(canvasId, type, data) {
    if (charts[canvasId]) charts[canvasId].destroy();
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;

    charts[canvasId] = new Chart(ctx, {
        type,
        data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: { color: '#9ca3af', font: { size: 11 } },
                    position: type === 'doughnut' ? 'right' : 'top',
                },
            },
            scales: type === 'doughnut' ? {} : {
                x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' }, beginAtZero: true },
            },
        },
    });
}

// ─── Keyboard Shortcuts ───────────────────────────────────────
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        closeDetail();
        closeReportDetail();
    }
});

// ─── Init ─────────────────────────────────────────────────────
connectWS();
loadSessions();
