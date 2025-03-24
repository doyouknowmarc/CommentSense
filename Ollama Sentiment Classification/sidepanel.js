// UI Elements
const elements = {
    videoTitle: document.getElementById('videoTitle'),
    llamaButton: document.getElementById('llamaButton'),
    spinner: document.getElementById('spinner'),
    totalComments: document.getElementById('totalComments'),
    positiveCount: document.getElementById('positiveCount'),
    neutralCount: document.getElementById('neutralCount'),
    negativeCount: document.getElementById('negativeCount'),
    includeTranscript: document.getElementById('includeTranscript'),
    transcriptContainer: document.getElementById('transcriptContainer'),
    transcriptContent: document.getElementById('transcriptContent')
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
    elements.llamaButton.addEventListener('click', () => startAnalysis('llama'));

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
    elements.llamaButton.disabled = true;

    // Reset filter to 'all'
    document.querySelector('input[name="sentimentFilter"][value="all"]').checked = true;

    // Get the transcript if checkbox is checked
    const includeTranscript = elements.includeTranscript.checked;
    const transcript = includeTranscript ? elements.transcriptContent.textContent : '';

    // Send analysis request
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const displayMode = document.querySelector('input[name="displayMode"]:checked')?.value || 'tag';
        chrome.tabs.sendMessage(tabs[0].id, {
            action: 'startAnalysis',
            modelType: modelType,
            displayMode: displayMode,
            transcript: transcript 
        });
    });
}

// Update the transcript checkbox handler with better error handling
elements.includeTranscript.addEventListener('change', async (e) => {
    console.log('Checkbox changed:', e.target.checked);
    elements.transcriptContainer.style.display = e.target.checked ? 'block' : 'none';
    
    if (e.target.checked) {
        try {
            console.log('Sending getTranscript request');
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            const url = new URL(tabs[0].url);
            const videoId = url.searchParams.get('v');
            
            if (!videoId) {
                throw new Error('Could not find video ID');
            }

            const response = await fetch('http://localhost:8002/get_transcript', {
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

// Update message listener to remove unused handlers
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
        elements.llamaButton.disabled = false;
    } else if (message.action === 'analysisError') {
        alert(`Analysis failed: ${message.error}\nPlease make sure the server is running and try again.`);
        
        // Reset UI state
        elements.spinner.style.display = 'none';
        elements.llamaButton.disabled = false;
    }
});