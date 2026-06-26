// Global API URL based on environment (relative for Cloudflare Pages)
const API_BASE = '/api';

// Utility for fetching data
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (e) {
        console.error('Fetch error:', e);
        return null;
    }
}

// Format date relative to now
function timeAgo(dateString) {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.round((now - date) / 1000);
    const minutes = Math.round(seconds / 60);
    const hours = Math.round(minutes / 60);
    const days = Math.round(hours / 24);

    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
}

// Create channel badge
function getNeutralityBadge(label) {
    const badgeClass = {
        'NEUTRAL': 'badge-neutral',
        'LEFT': 'badge-left',
        'RIGHT': 'badge-right'
    }[label] || 'badge-neutral';
    
    return `<span class="badge ${badgeClass}">${label || 'UNKNOWN'}</span>`;
}

// -----------------------------------------------------------------------------
// DASHBOARD LOGIC
// -----------------------------------------------------------------------------
async function initDashboard() {
    const grid = document.getElementById('channels-grid');
    if (!grid) return;

    let allChannels = [];

    // Setup filtering
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderChannels(allChannels, e.target.dataset.filter);
        });
    });

    // Fetch and render
    allChannels = await fetchAPI('/channels');
    if (allChannels && allChannels.length > 0) {
        renderChannels(allChannels, 'all');
    } else {
        grid.innerHTML = `
            <div class="loading-state">
                <p>No channels have been analyzed yet.</p>
                <p class="text-secondary" style="font-size:0.9rem;margin-top:0.5rem">Check back later once the Antigravity Agent finishes processing videos.</p>
            </div>
        `;
    }
}

function renderChannels(channels, filter) {
    const grid = document.getElementById('channels-grid');
    if (!grid) return;

    grid.innerHTML = '';
    
    const filtered = filter === 'all' 
        ? channels 
        : channels.filter(c => c.neutrality_label === filter);

    if (filtered.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:2rem"><p class="text-secondary">No channels match this filter.</p></div>';
        return;
    }

    // Sort by score descending
    filtered.sort((a, b) => (b.score || 0) - (a.score || 0));

    filtered.forEach(channel => {
        const card = document.createElement('a');
        card.href = `/channel.html?id=${channel.id}`;
        card.className = 'card';
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title">
                    <h3>${channel.name}</h3>
                    <p class="text-secondary">${channel.handle || ''}</p>
                </div>
                <div class="card-score">${(channel.score || 0).toFixed(1)}</div>
            </div>
            <div style="margin-bottom: 1.5rem">
                ${getNeutralityBadge(channel.neutrality_label)}
            </div>
            <div class="card-stats">
                <div class="stat">
                    <span class="stat-label">Last Evaluated</span>
                    <span>${timeAgo(channel.last_updated_time)}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">View Details</span>
                    <span style="color:var(--accent-primary)">Explore &rarr;</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

// -----------------------------------------------------------------------------
// CHANNEL DETAIL LOGIC
// -----------------------------------------------------------------------------
async function initChannelView() {
    const urlParams = new URLSearchParams(window.location.search);
    const channelId = urlParams.get('id');
    
    if (!channelId) {
        window.location.href = '/';
        return;
    }

    const loader = document.getElementById('channel-loading');
    const content = document.getElementById('channel-content');
    
    // We must fetch the channels to get the metadata, and then the videos
    const [channels, videos] = await Promise.all([
        fetchAPI('/channels'),
        fetchAPI(`/channel/${channelId}/videos`)
    ]);

    loader.style.display = 'none';

    if (!channels || !videos) {
        content.innerHTML = '<div class="loading-state"><p>Error loading channel data.</p></div>';
        content.style.display = 'block';
        return;
    }

    const channel = channels.find(c => c.id === channelId);
    if (!channel) {
        content.innerHTML = '<div class="loading-state"><p>Channel not found.</p></div>';
        content.style.display = 'block';
        return;
    }

    // Populate header
    document.getElementById('channel-name').textContent = channel.name;
    document.getElementById('channel-handle').textContent = channel.handle || '';
    document.getElementById('channel-score').textContent = (channel.score || 0).toFixed(1);
    
    const neutralityBox = document.getElementById('channel-neutrality');
    neutralityBox.innerHTML = getNeutralityBadge(channel.neutrality_label);
    
    content.style.display = 'block';

    // Populate videos
    const videosList = document.getElementById('videos-list');
    if (videos.length === 0) {
        videosList.innerHTML = '<p class="text-secondary">No videos evaluated for this channel yet.</p>';
        return;
    }

    videosList.innerHTML = '';
    
    // Sort videos by rated_at descending
    videos.sort((a, b) => new Date(b.rated_at) - new Date(a.rated_at));

    videos.forEach(video => {
        const div = document.createElement('div');
        div.className = 'card video-card';
        
        div.innerHTML = `
            <img src="${video.thumbnail_url || 'https://via.placeholder.com/480x270?text=No+Thumbnail'}" alt="Thumbnail" class="video-thumbnail" loading="lazy">
            <div class="video-content">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem">
                    <h3 class="video-title">${video.title}</h3>
                    <div class="card-score" style="font-size:0.9rem">${(video.composite || 0).toFixed(1)}</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric">
                        <span class="metric-val">${video.quality || 0}</span>
                        <span class="metric-name">Qual</span>
                    </div>
                    <div class="metric">
                        <span class="metric-val">${video.credibility || 0}</span>
                        <span class="metric-name">Cred</span>
                    </div>
                    <div class="metric">
                        <span class="metric-val">${video.rationality || 0}</span>
                        <span class="metric-name">Logic</span>
                    </div>
                    <div class="metric">
                        <span class="metric-val">${video.neutrality || 0}</span>
                        <span class="metric-name">Bias</span>
                    </div>
                </div>
                
                <p class="video-summary">"${video.summary || 'No summary available.'}"</p>
                
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:auto">
                    ${getNeutralityBadge(video.neutrality_label)}
                    <span class="text-secondary" style="font-size:0.8rem">Rated ${timeAgo(video.rated_at)}</span>
                </div>
            </div>
        `;
        videosList.appendChild(div);
    });
}

// Router
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('channel.html')) {
        initChannelView();
    } else {
        initDashboard();
    }
});
