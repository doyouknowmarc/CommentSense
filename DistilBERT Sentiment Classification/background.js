// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
    // Configure side panel
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
});

// Message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'analyzeComment') {
        analyzeComment(message, sendResponse);
        return true;
    } else if (message.action === 'getVideoTitle') {
        getVideoTitle(sendResponse);
        return true;
    } else if (message.action === 'getTranscript') {
        getTranscript(sendResponse);
        return true;
    }
});


// Get video title from active tab
async function getVideoTitle(sendResponse) {
    try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) {
            throw new Error('No active tab found');
        }

        const results = await chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            func: () => {
                const titleElement = document.querySelector('h1.ytd-watch-metadata yt-formatted-string');
                return titleElement ? titleElement.textContent.trim() : 'No video found';
            }
        });

        sendResponse({ title: results[0]?.result || 'Unable to fetch title' });
    } catch (error) {
        console.error('Error getting video title:', error);
        sendResponse({ title: 'Error fetching title' });
    }
}

// Handle comment analysis
async function analyzeComment(message, sendResponse) {
    const { comment, modelType, transcript } = message;
    
    try {
        if (!comment) {
            throw new Error('Comment is required');
        }

        // Get video ID from current tab URL
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        const url = new URL(tabs[0].url);
        const videoId = url.searchParams.get('v');

        const response = await fetch('http://localhost:8001/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                comment,
                video_id: videoId
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }

        const result = await response.json();
        if (!result.sentiment) {
            throw new Error('Invalid server response: missing sentiment');
        }

        sendResponse(result);
    } catch (error) {
        console.error('Error analyzing comment:', error);
        sendResponse({ error: error.message });
    }
}