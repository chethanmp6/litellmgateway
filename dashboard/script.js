// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Global variables to store charts
let modelUsageChart, costChart, responseTimeChart, tokenChart;
let dashboardData = {};

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        refreshDashboard(false); // Silent refresh
    }, 30000);
});

// Initialize dashboard
async function initializeDashboard() {
    showLoading();
    await Promise.all([
        loadOverviewMetrics(),
        loadModelAnalytics(),
        loadRecentSessions(),
        checkSystemHealth()
    ]);
    hideLoading();
    updateLastUpdateTime();
}

// Show loading state
function showLoading() {
    document.body.style.cursor = 'wait';
}

// Hide loading state
function hideLoading() {
    document.body.style.cursor = 'default';
}

// Load overview metrics
async function loadOverviewMetrics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/analytics/overview?days=7`);
        const data = await response.json();
        dashboardData.overview = data;
        renderOverviewMetrics(data);
    } catch (error) {
        console.error('Error loading overview metrics:', error);
        renderErrorMetrics();
    }
}

// Render overview metrics
function renderOverviewMetrics(data) {
    const metricsHtml = `
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="card metric-card h-100">
                <div class="card-body text-center">
                    <div class="metric-value text-primary">${data.total_requests || 0}</div>
                    <div class="metric-label">Total Requests</div>
                    <small class="text-muted">Last 7 days</small>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="card metric-card h-100">
                <div class="card-body text-center">
                    <div class="metric-value text-success">${data.unique_sessions || 0}</div>
                    <div class="metric-label">Unique Sessions</div>
                    <small class="text-muted">Active conversations</small>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="card metric-card h-100">
                <div class="card-body text-center">
                    <div class="metric-value text-warning">$${(data.total_cost || 0).toFixed(4)}</div>
                    <div class="metric-label">Total Cost</div>
                    <small class="text-muted">${(data.total_tokens || 0).toLocaleString()} tokens</small>
                </div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="card metric-card h-100">
                <div class="card-body text-center">
                    <div class="metric-value text-info">${(data.avg_response_time || 0).toFixed(2)}s</div>
                    <div class="metric-label">Avg Response Time</div>
                    <small class="text-muted">${(data.cache_hit_rate || 0)}% cache hit rate</small>
                </div>
            </div>
        </div>
    `;
    document.getElementById('overviewMetrics').innerHTML = metricsHtml;
}

// Render error state for metrics
function renderErrorMetrics() {
    const errorHtml = `
        <div class="col-12">
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Unable to load overview metrics. Please check your API connection.
            </div>
        </div>
    `;
    document.getElementById('overviewMetrics').innerHTML = errorHtml;
}

// Load model analytics and create charts
async function loadModelAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/analytics/models?days=7`);
        const models = await response.json();
        dashboardData.models = models;

        createModelUsageChart(models);
        createCostChart(models);
        createResponseTimeChart(models);
        createTokenChart(models);
    } catch (error) {
        console.error('Error loading model analytics:', error);
        renderChartErrors();
    }
}

// Create model usage pie chart
function createModelUsageChart(models) {
    const ctx = document.getElementById('modelUsageChart').getContext('2d');

    // Destroy existing chart if it exists
    if (modelUsageChart) {
        modelUsageChart.destroy();
    }

    const data = models.filter(m => m.total_requests > 0);

    modelUsageChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(m => m.model),
            datasets: [{
                data: data.map(m => m.total_requests),
                backgroundColor: [
                    '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
                    '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} requests (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Create cost breakdown chart
function createCostChart(models) {
    const ctx = document.getElementById('costChart').getContext('2d');

    if (costChart) {
        costChart.destroy();
    }

    const data = models.filter(m => m.total_cost > 0);

    costChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(m => m.model),
            datasets: [{
                label: 'Cost ($)',
                data: data.map(m => m.total_cost),
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(4);
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Cost: $${context.raw.toFixed(4)}`;
                        }
                    }
                }
            }
        }
    });
}

// Create response time chart
function createResponseTimeChart(models) {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');

    if (responseTimeChart) {
        responseTimeChart.destroy();
    }

    const data = models.filter(m => m.avg_response_time > 0);

    responseTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(m => m.model),
            datasets: [{
                label: 'Avg Response Time',
                data: data.map(m => m.avg_response_time),
                borderColor: 'rgba(231, 76, 60, 1)',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                fill: true,
                tension: 0.4
            }, {
                label: 'Max Response Time',
                data: data.map(m => m.max_response_time),
                borderColor: 'rgba(241, 196, 15, 1)',
                backgroundColor: 'rgba(241, 196, 15, 0.1)',
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    }
                }
            }
        }
    });
}

// Create token usage chart
function createTokenChart(models) {
    const ctx = document.getElementById('tokenChart').getContext('2d');

    if (tokenChart) {
        tokenChart.destroy();
    }

    const data = models.filter(m => m.total_tokens > 0);
    const promptTokens = data.map(m => m.total_prompt_tokens);
    const completionTokens = data.map(m => m.total_completion_tokens);

    tokenChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(m => m.model.split('-')[0]), // Shorter labels
            datasets: [{
                label: 'Prompt Tokens',
                data: promptTokens,
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1
            }, {
                label: 'Completion Tokens',
                data: completionTokens,
                backgroundColor: 'rgba(155, 89, 182, 0.7)',
                borderColor: 'rgba(155, 89, 182, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toLocaleString()} tokens`;
                        }
                    }
                }
            }
        }
    });
}

// Load recent sessions
async function loadRecentSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/sessions/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        const sessions = await response.json();
        dashboardData.sessions = sessions;
        renderSessionResults(sessions.slice(0, 10)); // Show first 10
    } catch (error) {
        console.error('Error loading sessions:', error);
        renderSessionError();
    }
}

// Search sessions with filters
async function searchSessions() {
    const filters = {
        user_id: document.getElementById('userFilter').value || undefined,
        model: document.getElementById('modelFilter').value || undefined,
        min_cost: parseFloat(document.getElementById('minCostFilter').value) || undefined,
        max_cost: parseFloat(document.getElementById('maxCostFilter').value) || undefined
    };

    // Remove undefined values
    Object.keys(filters).forEach(key =>
        filters[key] === undefined && delete filters[key]
    );

    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/api/v1/sessions/search?limit=20`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filters)
        });
        const sessions = await response.json();
        renderSessionResults(sessions);
        hideLoading();
    } catch (error) {
        console.error('Error searching sessions:', error);
        renderSessionError();
        hideLoading();
    }
}

// Render session results
function renderSessionResults(sessions) {
    if (!sessions || sessions.length === 0) {
        document.getElementById('sessionResults').innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>No sessions found matching your criteria.
            </div>
        `;
        return;
    }

    const sessionsHtml = sessions.map(session => `
        <div class="session-card card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <div class="d-flex align-items-center mb-2">
                            <strong class="me-3">${session.session_id.substring(0, 8)}...</strong>
                            <span class="badge bg-primary me-2">${session.user_id}</span>
                            ${session.models_used.map(model =>
                                `<span class="badge bg-secondary model-badge me-1">${model}</span>`
                            ).join('')}
                        </div>
                        <small class="text-muted">
                            <i class="fas fa-clock me-1"></i>${new Date(session.session_start).toLocaleString()}
                        </small>
                    </div>
                    <div class="col-md-4 text-end">
                        <div class="row">
                            <div class="col-6">
                                <div class="small text-muted">Messages</div>
                                <strong>${session.total_messages}</strong>
                            </div>
                            <div class="col-6">
                                <div class="small text-muted">Cost</div>
                                <strong>$${session.total_cost.toFixed(4)}</strong>
                            </div>
                        </div>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewSessionDetails('${session.session_id}')">
                                <i class="fas fa-eye me-1"></i>Details
                            </button>
                        </div>
                    </div>
                </div>
                <div class="progress mt-2" style="height: 4px;">
                    <div class="progress-bar" role="progressbar"
                         style="width: ${Math.min(session.total_cost * 10000, 100)}%"
                         title="Cost relative to max"></div>
                </div>
            </div>
        </div>
    `).join('');

    document.getElementById('sessionResults').innerHTML = `
        <div class="mb-3">
            <h6><i class="fas fa-list me-2"></i>Found ${sessions.length} session${sessions.length !== 1 ? 's' : ''}</h6>
        </div>
        ${sessionsHtml}
    `;
}

// Render session error
function renderSessionError() {
    document.getElementById('sessionResults').innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            Error loading sessions. Please check your API connection.
        </div>
    `;
}

// View session details (modal or separate view)
async function viewSessionDetails(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/summary`);
        const session = await response.json();

        const messagesResponse = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/messages`);
        const messages = await messagesResponse.json();

        // Create modal with session details
        showSessionModal(session, messages);
    } catch (error) {
        console.error('Error loading session details:', error);
        alert('Error loading session details');
    }
}

// Show session details modal
function showSessionModal(session, messages) {
    const modalHtml = `
        <div class="modal fade" id="sessionModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Session Details: ${session.session_id.substring(0, 16)}...</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>User:</strong> ${session.user_id}<br>
                                <strong>Agent:</strong> ${session.agent_name}<br>
                                <strong>Models:</strong> ${session.models_used.join(', ')}
                            </div>
                            <div class="col-md-6">
                                <strong>Total Cost:</strong> $${session.total_cost.toFixed(4)}<br>
                                <strong>Total Tokens:</strong> ${session.total_tokens.toLocaleString()}<br>
                                <strong>Duration:</strong> ${session.total_duration_seconds.toFixed(1)}s
                            </div>
                        </div>
                        <h6>Messages (${messages.length})</h6>
                        <div class="message-list" style="max-height: 400px; overflow-y: auto;">
                            ${messages.map((msg, index) => `
                                <div class="card mb-2">
                                    <div class="card-body py-2">
                                        <div class="d-flex justify-content-between">
                                            <strong>Message ${index + 1} - ${msg.model}</strong>
                                            <small class="text-muted">${new Date(msg.timestamp).toLocaleString()}</small>
                                        </div>
                                        <div class="row mt-2">
                                            <div class="col-md-4">
                                                <small class="text-muted">Tokens:</small> ${msg.total_tokens}
                                            </div>
                                            <div class="col-md-4">
                                                <small class="text-muted">Cost:</small> $${msg.cost.toFixed(4)}
                                            </div>
                                            <div class="col-md-4">
                                                <small class="text-muted">Time:</small> ${msg.response_time_seconds.toFixed(2)}s
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal
    const existingModal = document.getElementById('sessionModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('sessionModal'));
    modal.show();
}

// Check system health
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();

        document.getElementById('apiStatus').textContent = health.status === 'healthy' ? 'Healthy' : 'Unhealthy';
        document.getElementById('dbStatus').textContent = health.database === 'connected' ? 'Connected' : 'Disconnected';

    } catch (error) {
        console.error('Error checking system health:', error);
        document.getElementById('apiStatus').textContent = 'Error';
        document.getElementById('dbStatus').textContent = 'Error';
    }
}

// Update last update time
function updateLastUpdateTime() {
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
}

// Refresh dashboard
async function refreshDashboard(showLoading = true) {
    if (showLoading) {
        showLoading();
    }

    await initializeDashboard();

    if (showLoading) {
        hideLoading();
    }
}

// Render chart errors
function renderChartErrors() {
    ['modelUsageChart', 'costChart', 'responseTimeChart', 'tokenChart'].forEach(chartId => {
        const canvas = document.getElementById(chartId);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#e74c3c';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Error loading chart data', canvas.width / 2, canvas.height / 2);
    });
}