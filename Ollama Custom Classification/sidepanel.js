// UI Elements
const elements = {
    videoTitle: document.getElementById('videoTitle'),
    analyzeButton: document.getElementById('analyzeButton'),
    spinner: document.getElementById('spinner'),
    totalComments: document.getElementById('totalComments'),
    sentimentStats: document.getElementById('sentimentStats'),
    toneStats: document.getElementById('toneStats'),
    flagStats: document.getElementById('flagStats'),
    includeTranscript: document.getElementById('includeTranscript'),
    transcriptContainer: document.getElementById('transcriptContainer'),
    transcriptContent: document.getElementById('transcriptContent'),
    sentimentFilters: document.getElementById('sentimentFilters'),
    toneFilters: document.getElementById('toneFilters'),
    flagFilters: document.getElementById('flagFilters')
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Request video title update
    chrome.runtime.sendMessage({ action: 'getVideoTitle' }, (response) => {
        if (response && response.title) {
            elements.videoTitle.textContent = response.title;
        }
    });

    // Add click handler for analysis button
    elements.analyzeButton.addEventListener('click', startAnalysis);

    // Add event listeners for YouTube controls
    const cinemaModeToggle = document.getElementById('cinemaModeToggle');
    const hideSuggestedToggle = document.getElementById('hideSuggestedToggle');

    cinemaModeToggle.addEventListener('change', (e) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: 'toggleCinemaMode',
                enabled: e.target.checked
            });
        });
    });

    hideSuggestedToggle.addEventListener('change', (e) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: 'toggleSuggestedVideos',
                hidden: e.target.checked
            });
        });
    });
});

// Function to update filter options
function updateFilterOptions(stats) {
    // Update sentiment filters
    const sentimentHtml = Object.keys(stats.sentiment).map(sentiment => `
        <label>
            <input type="radio" name="sentimentFilter" value="${sentiment}"> ${sentiment}
        </label>
    `).join('');
    elements.sentimentFilters.innerHTML = `
        <label><input type="radio" name="sentimentFilter" value="all" checked> Show All</label>
        ${sentimentHtml}
    `;

    // Update tone filters
    const toneHtml = Object.keys(stats.tone).map(tone => `
        <label>
            <input type="checkbox" name="toneFilter" value="${tone}"> ${tone}
        </label>
    `).join('');
    elements.toneFilters.innerHTML = toneHtml;

    // Update special flags filters
    const flagHtml = Object.keys(stats.special_flags).map(flag => `
        <label>
            <input type="checkbox" name="flagFilter" value="${flag}"> ${flag}
        </label>
    `).join('');
    elements.flagFilters.innerHTML = flagHtml;

    // Add event listeners for filters
    document.querySelectorAll('input[name="sentimentFilter"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'filterComments',
                    filterType: 'sentiment',
                    value: e.target.value,
                    show: true
                });
            });
        });
    });

    // Update tone filter handler
    document.querySelectorAll('input[name="toneFilter"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const selectedTones = Array.from(document.querySelectorAll('input[name="toneFilter"]:checked'))
                .map(cb => cb.value);
            
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'filterComments',
                    filterType: 'tone',
                    value: selectedTones.length > 0 ? selectedTones.join(',') : 'all',
                    show: true
                });
            });
        });
    });

    // Update special flags filter handler
    document.querySelectorAll('input[name="flagFilter"]').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const selectedFlags = Array.from(document.querySelectorAll('input[name="flagFilter"]:checked'))
                .map(cb => cb.value);
            
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'filterComments',
                    filterType: 'special-flag',
                    value: selectedFlags.length > 0 ? selectedFlags.join(',') : 'all',
                    show: true
                });
            });
        });
    });
}

// Function to update statistics display
function updateStats(stats) {
    elements.totalComments.textContent = stats.total;

    // Update sentiment stats
    elements.sentimentStats.innerHTML = Object.entries(stats.sentiment)
        .map(([sentiment, count]) => `<p>${sentiment}: ${count}</p>`)
        .join('');

    // Update tone stats
    elements.toneStats.innerHTML = Object.entries(stats.tone)
        .map(([tone, count]) => `<p>${tone}: ${count}</p>`)
        .join('');

    // Update special flags stats
    elements.flagStats.innerHTML = Object.entries(stats.special_flags)
        .map(([flag, count]) => `<p>${flag}: ${count}</p>`)
        .join('');
}

// Function to start analysis
function startAnalysis() {
    // Show loading state
    elements.spinner.style.display = 'block';
    elements.analyzeButton.disabled = true;

    // Reset filters
    const allFilterRadio = document.querySelector('input[name="sentimentFilter"][value="all"]');
    if (allFilterRadio) {
        allFilterRadio.checked = true;
    }

    // Get the transcript if checkbox is checked
    const includeTranscript = elements.includeTranscript.checked;
    const transcript = includeTranscript ? elements.transcriptContent.textContent : '';

    // Send analysis request
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {
            action: 'startAnalysis',
            transcript: transcript
        });
    });
}

// Update the transcript checkbox handler
elements.includeTranscript.addEventListener('change', async (e) => {
    elements.transcriptContainer.style.display = e.target.checked ? 'block' : 'none';
    
    if (e.target.checked) {
        try {
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            const url = new URL(tabs[0].url);
            const videoId = url.searchParams.get('v');
            
            if (!videoId) {
                throw new Error('Could not find video ID');
            }

            const response = await fetch('http://localhost:8003/get_transcript', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_id: videoId })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load transcript: ${response.status}`);
            }

            const data = await response.json();
            elements.transcriptContent.textContent = data.transcript;
        } catch (error) {
            console.error('Transcript error:', error);
            elements.transcriptContent.textContent = `Error: ${error.message}`;
        }
    } else {
        elements.transcriptContent.textContent = '';
    }
});

// Update message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'updateVideoTitle' && message.title) {
        elements.videoTitle.textContent = message.title;
    } else if (message.action === 'analysisComplete') {
        // Update UI with results
        updateStats(message.stats);
        updateFilterOptions(message.stats);

        // Reset UI state
        elements.spinner.style.display = 'none';
        elements.analyzeButton.disabled = false;
    } else if (message.action === 'analysisError') {
        // Handle error
        alert(`Analysis failed: ${message.error}\nPlease make sure the server is running and try again.`);
        
        // Reset UI state
        elements.spinner.style.display = 'none';
        elements.analyzeButton.disabled = false;
    }
});