const API_BASE = '/api';

let priceChart, basisChart;
let currentPair = 'BTC_USDT';

async function fetchPairs() {
    const res = await fetch(`${API_BASE}/pairs`);
    const pairs = await res.json();
    const select = document.getElementById('pairSelect');
    select.innerHTML = pairs.map(p => `<option value="${p}" ${p === currentPair ? 'selected' : ''}>${p}</option>`).join('');
}

async function fetchConfig() {
    const res = await fetch(`${API_BASE}/config`);
    const config = await res.json();
    if (config.current_pair) {
        currentPair = config.current_pair;
        document.getElementById('pairSelect').value = currentPair;
    }
}

async function saveConfig() {
    const newPair = document.getElementById('pairSelect').value;
    await fetch(`${API_BASE}/config`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ current_pair: newPair })
    });
    currentPair = newPair;
    loadData();
}

async function fetchSummary() {
    const res = await fetch(`${API_BASE}/stats/summary?pair=${currentPair}`);
    return res.json();
}

async function fetchBasis(minutes = 60) {
    const res = await fetch(`${API_BASE}/stats/basis?pair=${currentPair}&minutes=${minutes}`);
    return res.json();
}

async function fetchLargeTrades(limit = 20) {
    const res = await fetch(`${API_BASE}/stats/large_trades?pair=${currentPair}&limit=${limit}`);
    return res.json();
}

function updateSummary(data) {
    document.getElementById('spotPrice').innerText = data.spot_price?.toFixed(2) ?? '-';
    document.getElementById('futuresPrice').innerText = data.futures_price?.toFixed(2) ?? '-';
    document.getElementById('basisPercent').innerText = data.basis_percent?.toFixed(3) + '%' ?? '-';
    document.getElementById('largeCount').innerText = data.large_trades_1h ?? 0;
}

function renderPriceChart(basisData) {
    if (!basisData || basisData.length === 0) return;
    const labels = basisData.map(b => new Date(b.timestamp * 1000).toLocaleTimeString());
    const spotPrices = basisData.map(b => b.spot_price);
    const futuresPrices = basisData.map(b => b.futures_price);
    
    if (priceChart) priceChart.destroy();
    const ctx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'Spot', data: spotPrices, borderColor: 'blue', fill: false },
                { label: 'Futures', data: futuresPrices, borderColor: 'orange', fill: false }
            ]
        },
        options: { responsive: true }
    });
}

function renderBasisChart(basisData) {
    if (!basisData || basisData.length === 0) return;
    const labels = basisData.map(b => new Date(b.timestamp * 1000).toLocaleTimeString());
    const basisPercents = basisData.map(b => b.basis_percent);
    
    const mean = basisPercents.reduce((a,b) => a+b,0)/basisPercents.length;
    const std = Math.sqrt(basisPercents.map(x => Math.pow(x-mean,2)).reduce((a,b)=>a+b,0)/basisPercents.length);
    
    if (basisChart) basisChart.destroy();
    const ctx = document.getElementById('basisChart').getContext('2d');
    basisChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'Basis %', data: basisPercents, borderColor: 'green', fill: false },
                { label: 'Mean', data: Array(labels.length).fill(mean), borderColor: 'gray', borderDash: [5,5], fill: false },
                { label: '+1σ', data: Array(labels.length).fill(mean+std), borderColor: 'lightgreen', borderDash: [2,2], fill: false },
                { label: '-1σ', data: Array(labels.length).fill(mean-std), borderColor: 'lightcoral', borderDash: [2,2], fill: false }
            ]
        },
        options: { responsive: true }
    });
}

function renderLargeTrades(trades) {
    const tbody = document.querySelector('#largeTradesTable tbody');
    tbody.innerHTML = trades.map(t => `
        <tr>
            <td>${new Date(t.timestamp * 1000).toLocaleString()}</td>
            <td>${t.price}</td>
            <td>${t.volume.toFixed(2)}</td>
            <td style="color: ${t.side === 'buy' ? 'green' : 'red'}">${t.side}</td>
        </tr>
    `).join('');
}

async function loadData() {
    const [summary, basis, largeTrades] = await Promise.all([
        fetchSummary(),
        fetchBasis(60),
        fetchLargeTrades(20)
    ]);
    updateSummary(summary);
    renderPriceChart(basis);
    renderBasisChart(basis);
    renderLargeTrades(largeTrades);
}

window.onload = async () => {
    await fetchPairs();
    await fetchConfig();
    loadData();
    setInterval(loadData, 10000);
    
    document.getElementById('saveConfig').addEventListener('click', saveConfig);
};
