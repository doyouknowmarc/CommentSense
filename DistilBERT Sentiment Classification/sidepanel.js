// UI Elements
const elements = {
    videoTitle: document.getElementById('videoTitle'),
    bertButton: document.getElementById('bertButton'),
    spinner: document.getElementById('spinner'),
    totalComments: document.getElementById('totalComments'),
    positiveCount: document.getElementById('positiveCount'),
    neutralCount: document.getElementById('neutralCount'),
    negativeCount: document.getElementById('negativeCount')
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Request video title update
    chrome.runtime.sendMessage({ action: 'getVideoTitle' }, (response) => {
        if (response && response.title) {
            elements.videoTitle.textContent = response.title;
        }
    });

    // Add click handlers for analysis buttons
    elements.bertButton.addEventListener('click', () => startAnalysis('bert'));

    // Add event listeners for sentiment filters
    document.querySelectorAll('input[name="sentimentFilter"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'filterComments',
                    sentiment: e.target.value,
                    show: true
                });
            });
        });
    });
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

// Function to start analysis
function startAnalysis(modelType) {
    // Show loading state
    elements.spinner.style.display = 'block';
    elements.bertButton.disabled = true;

    // Reset filter to 'all'
    document.querySelector('input[name="sentimentFilter"][value="all"]').checked = true;

    // Send analysis request
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.sendMessage(tabs[0].id, {
            action: 'startAnalysis',
            modelType: modelType,
            displayMode: 'tag'  // Always use tag mode for consistent display
        }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error starting analysis:', chrome.runtime.lastError);
                elements.spinner.style.display = 'none';
                elements.bertButton.disabled = false;
                alert('Failed to start analysis. Please try again.');
            }
        });
    });
}

// Update message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Received message:', message);
    if (message.action === 'updateVideoTitle' && message.title) {
        elements.videoTitle.textContent = message.title;
    } else if (message.action === 'analysisComplete') {
        // Update UI with results
        elements.totalComments.textContent = message.stats.total;
        elements.positiveCount.textContent = message.stats.positive;
        elements.neutralCount.textContent = message.stats.neutral;
        elements.negativeCount.textContent = message.stats.negative;

        // Reset UI state
        elements.spinner.style.display = 'none';
        elements.bertButton.disabled = false;
    } else if (message.action === 'analysisError') {
        // Handle error
        alert(`Analysis failed: ${message.error}\nPlease make sure the server is running and try again.`);
        
        // Reset UI state
        elements.spinner.style.display = 'none';
        elements.bertButton.disabled = false;
    }
});