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


async function getTranscript(sendResponse) {  
    try {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) {
            throw new Error('No active tab found');
        }

        // Get video ID from content script
        const results = await chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            func: () => {
                const url = window.location.href;
                const videoId = url.split('v=')[1]?.split('&')[0];
                return videoId;
            }
        });

        const videoId = results[0]?.result;
        if (!videoId) {
            throw new Error('Could not get video ID');
        }

        // Send request to your server
        const response = await fetch('http://localhost:8003/get_transcript', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: videoId })
        });

        if (!response.ok) {
            throw new Error('Failed to get transcript');
        }

        const data = await response.json();
        
        // Send transcript back to sidepanel instead of content script
        sendResponse({ transcript: data.transcript });

    } catch (error) {
        console.error('Error getting transcript:', error);
        sendResponse({ error: error.message });
    }
}

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
    const { comment, transcript, classNames, classExamples } = message;
    
    try {
        if (!comment) {
            throw new Error('Comment is required');
        }

        // Get video ID from current tab URL
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        const url = new URL(tabs[0].url);
        const videoId = url.searchParams.get('v');

        const response = await fetch('http://localhost:8003/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                comment,
                model: 'mistral-small:22b',
                transcript: transcript,
                video_id: videoId,
                classNames: classNames,
                classExamples: classExamples
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }

        const result = await response.json();
        if (!result.sentiment || !result.tone) {
            throw new Error('Invalid server response: missing sentiment or tone classification');
        }

        sendResponse(result);
    } catch (error) {
        console.error('Error analyzing comment:', error);
        sendResponse({ error: error.message });
    }
}