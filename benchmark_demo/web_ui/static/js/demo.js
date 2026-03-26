// Soplex AI Demo JavaScript
class SoplexDemo {
    constructor() {
        this.isRunning = false;
        this.pollInterval = null;
        this.progressSteps = ['traditional', 'soplex', 'compare'];
        this.currentStepIndex = 0;

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.startBtn = document.getElementById('startDemo');
        this.demoStatus = document.getElementById('demoStatus');
        this.statusIndicator = this.demoStatus.querySelector('.status-indicator');
        this.statusText = this.demoStatus.querySelector('.status-text');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressFill = document.getElementById('progressFill');
        this.logsContainer = document.getElementById('logsContainer');
        this.logsOutput = document.getElementById('logsOutput');
        this.resultsSection = document.getElementById('resultsSection');
        this.metricsGrid = document.getElementById('metricsGrid');
        this.liveResults = document.getElementById('liveResults');
        this.loadGraphBtn = document.getElementById('loadGraph');
        this.graphVisualization = document.getElementById('graphVisualization');
        this.graphStats = document.getElementById('graphStats');
        this.graphStatus = document.getElementById('graphStatus');
    }

    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startDemo());
        this.loadGraphBtn.addEventListener('click', () => this.loadGraphVisualization());
    }

    async startDemo() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.startBtn.disabled = true;
        this.startBtn.textContent = 'Running Demo...';

        this.showProgressBar();
        this.showLogs();
        this.showLiveResults();
        this.hideResults();

        // Start the backend comparison
        try {
            const response = await fetch('/start_comparison', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.updateStatus('Demo started successfully', 'running');
                this.startPolling();
            } else {
                throw new Error('Failed to start demo');
            }
        } catch (error) {
            console.error('Error starting demo:', error);
            this.updateStatus('Error starting demo', 'error');
            this.resetDemo();
        }
    }

    startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch('/demo_status');
                const data = await response.json();

                this.updateProgress(data);
                this.updateLogs(data.logs);

                if (!data.running) {
                    this.stopPolling();
                    if (data.traditional && data.soplex) {
                        await this.showResults();
                    } else {
                        this.updateStatus('Demo completed with errors', 'error');
                    }
                    this.resetDemo();
                }
            } catch (error) {
                console.error('Error polling status:', error);
                this.stopPolling();
                this.resetDemo();
            }
        }, 1000);
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    updateStatus(message, type = 'ready') {
        this.statusText.textContent = message;
        this.statusIndicator.className = `status-indicator ${type}`;
    }

    updateProgress(data) {
        if (data.current_step) {
            this.statusText.textContent = data.current_step;

            // Update progress based on current step
            let progress = 0;
            if (data.current_step.includes('Traditional')) {
                progress = 33;
                this.currentStepIndex = 0;
            } else if (data.current_step.includes('Soplex')) {
                progress = 66;
                this.currentStepIndex = 1;
            } else if (data.current_step.includes('Complete')) {
                progress = 100;
                this.currentStepIndex = 2;
            }

            this.progressFill.style.width = `${progress}%`;
            this.highlightCurrentStep();
        }
    }

    highlightCurrentStep() {
        const steps = document.querySelectorAll('.progress-steps .step');
        steps.forEach((step, index) => {
            if (index <= this.currentStepIndex) {
                step.style.color = 'var(--primary-color)';
                step.style.fontWeight = '600';
            } else {
                step.style.color = 'var(--text-secondary)';
                step.style.fontWeight = '500';
            }
        });
    }

    updateLogs(logs) {
        if (!logs || logs.length === 0) return;

        // Add new logs
        logs.forEach(log => {
            if (!this.logsOutput.textContent.includes(log)) {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.textContent = log;
                this.logsOutput.appendChild(logEntry);
            }
        });

        // Auto-scroll to bottom
        this.logsOutput.scrollTop = this.logsOutput.scrollHeight;
    }

    async showResults() {
        try {
            const response = await fetch('/generate_graphs');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update metrics
            this.updateMetrics(data.metrics);

            // Render charts
            this.renderChart('costChart', data.cost_chart);
            this.renderChart('callsChart', data.calls_chart);
            this.renderChart('timeChart', data.time_chart);

            // Show results section with animation
            this.resultsSection.style.display = 'block';
            this.resultsSection.style.opacity = '0';
            this.resultsSection.style.transform = 'translateY(20px)';

            setTimeout(() => {
                this.resultsSection.style.transition = 'all 0.8s ease';
                this.resultsSection.style.opacity = '1';
                this.resultsSection.style.transform = 'translateY(0)';
            }, 100);

            this.updateStatus('Comparison complete! 🎉', 'ready');

        } catch (error) {
            console.error('Error showing results:', error);
            this.updateStatus('Error generating results', 'error');
        }
    }

    updateMetrics(metrics) {
        const metricsHTML = `
            <div class="metric-card">
                <span class="metric-value">${metrics.cost_savings}%</span>
                <span class="metric-label">Cost Savings</span>
                <div class="metric-improvement">
                    $${metrics.traditional_cost.toFixed(4)} → $${metrics.soplex_cost.toFixed(4)}
                </div>
            </div>
            <div class="metric-card">
                <span class="metric-value">${metrics.time_savings}%</span>
                <span class="metric-label">Time Savings</span>
                <div class="metric-improvement">
                    ${metrics.traditional_time.toFixed(2)}s → ${metrics.soplex_time.toFixed(2)}s
                </div>
            </div>
            <div class="metric-card">
                <span class="metric-value">${metrics.call_reduction}%</span>
                <span class="metric-label">Fewer LLM Calls</span>
                <div class="metric-improvement">
                    Hybrid execution model
                </div>
            </div>
            <div class="metric-card">
                <span class="metric-value">99%+</span>
                <span class="metric-label">Accuracy</span>
                <div class="metric-improvement">
                    Deterministic logic
                </div>
            </div>
        `;
        this.metricsGrid.innerHTML = metricsHTML;
    }

    renderChart(containerId, chartData) {
        try {
            const parsedData = JSON.parse(chartData);
            Plotly.newPlot(containerId, parsedData.data, parsedData.layout, {
                responsive: true,
                displayModeBar: false
            });
        } catch (error) {
            console.error(`Error rendering chart ${containerId}:`, error);
        }
    }

    showProgressBar() {
        this.progressContainer.style.display = 'block';
        this.progressFill.style.width = '0%';
        this.currentStepIndex = 0;
    }

    showLogs() {
        this.logsContainer.style.display = 'block';
        this.logsOutput.innerHTML = '';
    }

    hideResults() {
        this.resultsSection.style.display = 'none';
    }

    showLiveResults() {
        if (this.liveResults) {
            this.liveResults.style.display = 'block';
        }
    }

    async loadGraphVisualization() {
        if (!this.loadGraphBtn) return;

        this.loadGraphBtn.disabled = true;
        this.loadGraphBtn.textContent = 'Loading Graph...';
        this.graphStatus.querySelector('.status-text').textContent = 'Loading compiled graph...';

        try {
            const response = await fetch('/graph_visualization');
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Show graph visualization
            this.graphVisualization.style.display = 'block';

            // Update stats
            this.updateGraphStats(data.stats);

            // Render interactive graph
            const graphData = JSON.parse(data.graph_data);
            Plotly.newPlot('interactiveGraph', graphData.data, graphData.layout, {
                responsive: true,
                displayModeBar: true
            });

            this.graphStatus.querySelector('.status-text').textContent =
                `Graph loaded: ${data.graph_file}`;

        } catch (error) {
            console.error('Error loading graph:', error);
            this.graphStatus.querySelector('.status-text').textContent =
                `Error: ${error.message}`;
        } finally {
            this.loadGraphBtn.disabled = false;
            this.loadGraphBtn.innerHTML = '<span class="btn-icon">🔍</span> Reload Graph';
        }
    }

    updateGraphStats(stats) {
        if (!stats || !this.graphStats) return;

        const statsHTML = `
            <div class="graph-stat-item">
                <span class="graph-stat-value">${stats.total_nodes || 0}</span>
                <span class="graph-stat-label">Total Nodes</span>
            </div>
            <div class="graph-stat-item">
                <span class="graph-stat-value">${stats.total_edges || 0}</span>
                <span class="graph-stat-label">Connections</span>
            </div>
            <div class="graph-stat-item">
                <span class="graph-stat-value">${stats.node_types?.llm || 0}</span>
                <span class="graph-stat-label">LLM Nodes</span>
            </div>
            <div class="graph-stat-item">
                <span class="graph-stat-value">${(stats.node_types?.code || 0) + (stats.node_types?.api || 0)}</span>
                <span class="graph-stat-label">Code/API Nodes</span>
            </div>
            <div class="graph-stat-item">
                <span class="graph-stat-value">${stats.cost_optimization?.optimization_level || 'Unknown'}</span>
                <span class="graph-stat-label">Optimization Level</span>
            </div>
        `;

        this.graphStats.innerHTML = statsHTML;

        // Add execution flow preview
        if (stats.execution_flow && stats.execution_flow.length > 0) {
            const flowHTML = `
                <div class="execution-flow-preview">
                    <h4>🔄 Execution Flow Preview</h4>
                    <div class="flow-steps-preview">
                        ${stats.execution_flow.map(step =>
                            `<span class="flow-step-preview">${step}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
            this.graphStats.innerHTML += flowHTML;
        }

        // Add legend
        const legendHTML = `
            <div class="node-type-legend">
                <div class="legend-item">
                    <div class="legend-color legend-llm"></div>
                    <span>🧠 LLM (Conversation)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-code"></div>
                    <span>⚡ Code (Logic)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-api"></div>
                    <span>🔌 API (External)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-branch"></div>
                    <span>🔀 Branch (Decision)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-end"></div>
                    <span>🎯 End (Terminal)</span>
                </div>
            </div>
        `;
        this.graphStats.innerHTML += legendHTML;
    }

    resetDemo() {
        this.isRunning = false;
        this.startBtn.disabled = false;
        this.startBtn.innerHTML = '<span class="btn-icon">⚡</span> Start Live Comparison';
        this.stopPolling();
    }
}

// Add some utility functions for animations
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

function createSparklineChart(containerId, data, color) {
    const trace = {
        x: data.x,
        y: data.y,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: color,
            width: 3
        },
        fill: 'tonexty',
        fillcolor: `${color}20`
    };

    const layout = {
        showlegend: false,
        margin: { l: 0, r: 0, t: 0, b: 0 },
        xaxis: { visible: false },
        yaxis: { visible: false },
        plot_bgcolor: 'transparent',
        paper_bgcolor: 'transparent'
    };

    Plotly.newPlot(containerId, [trace], layout, {
        responsive: true,
        displayModeBar: false
    });
}

// Initialize the demo when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.soplexDemo = new SoplexDemo();

    // Add some visual effects
    addFloatingParticles();
});

function addFloatingParticles() {
    // Create floating particle background effect
    const particlesContainer = document.createElement('div');
    particlesContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    `;

    document.body.appendChild(particlesContainer);

    // Create particles
    for (let i = 0; i < 20; i++) {
        createParticle(particlesContainer);
    }
}

function createParticle(container) {
    const particle = document.createElement('div');
    particle.style.cssText = `
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(78, 205, 196, 0.3);
        border-radius: 50%;
        animation: float ${5 + Math.random() * 10}s linear infinite;
        left: ${Math.random() * 100}%;
        animation-delay: ${Math.random() * 5}s;
    `;

    container.appendChild(particle);

    // Remove and recreate particle after animation
    setTimeout(() => {
        if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
            createParticle(container);
        }
    }, (5 + Math.random() * 10) * 1000);
}

// Add CSS animation for particles
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0% {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-10px) rotate(360deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);