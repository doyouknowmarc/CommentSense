// Function to send video title to sidepanel
function sendVideoTitle() {
    const titleElement = document.querySelector('h1.ytd-watch-metadata');
    if (titleElement) {
        chrome.runtime.sendMessage({ action: 'getVideoTitle' });
        // Disconnect observer once title is found
        if (observer) {
            observer.disconnect();
        }
    }
}

// Initialize video title extraction
document.addEventListener('DOMContentLoaded', sendVideoTitle);

// Create observer with a flag
let observer = new MutationObserver(() => {
    const titleElement = document.querySelector('h1.ytd-watch-metadata');
    if (titleElement) {
        sendVideoTitle();
        observer.disconnect();
    }
});

// Start observing with a more specific target
const targetNode = document.documentElement;
observer.observe(targetNode, {
    childList: true,
    subtree: true
});

// Function to scrape comments
function scrapeComments() {
    const commentElements = document.querySelectorAll('ytd-comment-thread-renderer #content #content-text');
    const comments = Array.from(commentElements)
        .map(element => element.textContent.trim())
        .filter(comment => comment !== '');

    return { 
        comments, 
        commentElements: Array.from(document.querySelectorAll('ytd-comment-thread-renderer'))
            .filter((_, i) => comments[i] !== '') 
    };
}

// Function to create a classification tag
function createClassTag(type, value, reasoning, model) {
    const tag = document.createElement('div');
    tag.className = `class-tag ${type}`;
    tag.style.cssText = `
        display: inline-block;
        padding: 4px 8px;
        margin: 4px 4px 4px 0;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
    `;
    
    // Set different background colors based on tag type
    switch(type) {
        case 'sentiment':
            tag.style.backgroundColor = '#e3f2fd';
            tag.style.borderColor = '#90caf9';
            break;
        case 'tone':
            tag.style.backgroundColor = '#f3e5f5';
            tag.style.borderColor = '#ce93d8';
            break;
        case 'special-flag':
            tag.style.backgroundColor = '#ffebee';
            tag.style.borderColor = '#ef9a9a';
            break;
    }
    
    // Get the specific reasoning for this type
    const specificReasoning = type === 'special-flag' 
        ? reasoning.special_flags 
        : reasoning[type.replace('-', '_')] || '';
    const detailsText = `${type.toUpperCase()}: ${value}\n${model}\nReasoning: ${specificReasoning}`;
    
    tag.textContent = value;
    tag.setAttribute('data-details', detailsText);
    tag.setAttribute('data-type', type);
    tag.setAttribute('data-value', value);
    
    tag.addEventListener('click', () => {
        tag.textContent = tag.textContent === value ? detailsText : value;
    });
    
    return tag;
}

// Function to highlight comment based on class
function highlightComment(commentElement, analysis, model) {
    commentElement.style.backgroundColor = '#f8f9fa';
    commentElement.style.padding = '12px';
    commentElement.style.borderRadius = '8px';
    commentElement.style.margin = '8px 0';

    // Create tags container
    const tagsContainer = document.createElement('div');
    tagsContainer.style.marginTop = '8px';
    tagsContainer.style.display = 'flex';
    tagsContainer.style.flexWrap = 'wrap';
    tagsContainer.style.gap = '4px';

    // Add sentiment tag
    tagsContainer.appendChild(
        createClassTag('sentiment', analysis.sentiment, analysis.reasoning, model)
    );

    // Add tone tags
    analysis.tone.forEach(tone => {
        tagsContainer.appendChild(
            createClassTag('tone', tone, analysis.reasoning, model)
        );
    });

    // Add special flags tags
    if (analysis.special_flags && analysis.special_flags.length > 0) {
        analysis.special_flags.forEach(flag => {
            tagsContainer.appendChild(
                createClassTag('special-flag', flag, analysis.reasoning, model)
            );
        });
    }

    // Add detailed analysis section
    const analysisSection = document.createElement('div');
    analysisSection.style.cssText = 'margin-top: 8px; padding: 8px; font-size: 12px; color: #666; display: none;';
    analysisSection.innerHTML = `
        <strong>Full Analysis:</strong><br>
        <strong>Model:</strong> ${model}<br>
        <strong>Sentiment Reasoning:</strong> ${analysis.reasoning.sentiment}<br>
        <strong>Tone Reasoning:</strong> ${analysis.reasoning.tone}<br>
        ${analysis.special_flags && analysis.special_flags.length > 0 
            ? `<strong>Special Flags Reasoning:</strong> ${analysis.reasoning.special_flags}` 
            : ''}
    `;

    // Add toggle button for detailed analysis
    const toggleButton = document.createElement('button');
    toggleButton.textContent = 'Show Analysis';
    toggleButton.style.cssText = 'margin-top: 8px; padding: 4px 8px; font-size: 12px; cursor: pointer;';
    toggleButton.onclick = () => {
        analysisSection.style.display = analysisSection.style.display === 'none' ? 'block' : 'none';
        toggleButton.textContent = analysisSection.style.display === 'none' ? 'Show Analysis' : 'Hide Analysis';
    };

    // Add all elements to comment
    commentElement.appendChild(tagsContainer);
    commentElement.appendChild(toggleButton);
    commentElement.appendChild(analysisSection);

    // Store classification data for filtering
    commentElement.setAttribute('data-sentiment', analysis.sentiment.toLowerCase());
    commentElement.setAttribute('data-tones', analysis.tone.map(t => t.toLowerCase()).join('|'));
    commentElement.setAttribute('data-flags', (analysis.special_flags || []).map(f => f.toLowerCase()).join('|'));
}

// Function to analyze comments
async function analyzeComments(displayMode = 'highlight', transcript = null) {
    try {
        const { comments, commentElements } = scrapeComments();
        if (comments.length === 0) {
            throw new Error('No comments found');
        }

        // Get video ID
        const url = new URL(window.location.href);
        const videoId = url.searchParams.get('v');

        const stats = {
            total: comments.length,
            sentiment: {},
            tone: {},
            special_flags: {}
        };

        for (let i = 0; i < comments.length; i++) {
            try {
                const response = await new Promise((resolve, reject) => {
                    chrome.runtime.sendMessage({
                        action: 'analyzeComment',
                        comment: comments[i],
                        transcript: transcript,
                        video_id: videoId
                    }, response => {
                        if (chrome.runtime.lastError) {
                            reject(chrome.runtime.lastError);
                        } else {
                            resolve(response);
                        }
                    });
                });

                if (response.error) {
                    throw new Error(response.error);
                }

                if (!response.sentiment && !response.class) {
                    throw new Error('Invalid server response: missing classification');
                }

                // Update stats
                stats.sentiment[response.sentiment] = (stats.sentiment[response.sentiment] || 0) + 1;
                response.tone.forEach(tone => {
                    stats.tone[tone] = (stats.tone[tone] || 0) + 1;
                });
                if (response.special_flags) {
                    response.special_flags.forEach(flag => {
                        stats.special_flags[flag] = (stats.special_flags[flag] || 0) + 1;
                    });
                }

                highlightComment(commentElements[i], response, 'mistral-small:22b');
            } catch (error) {
                console.error(`Error analyzing comment ${i + 1}:`, error);
                continue;
            }
        }

        // Send analysis completion message with stats
        chrome.runtime.sendMessage({
            action: 'analysisComplete',
            stats: stats
        });
    } catch (error) {
        console.error('Analysis failed:', error);
        chrome.runtime.sendMessage({
            action: 'analysisError',
            error: error.message
        });
    }
}

// Function to filter comments
function filterComments(type, value, show) {
    const commentElements = document.querySelectorAll('ytd-comment-thread-renderer');
    commentElements.forEach(element => {
        if (type === 'sentiment' && value === 'all' || 
            (type !== 'sentiment' && value === 'all')) {
            // Show all comments when 'Show All' is selected or no checkboxes are checked
            element.style.display = 'block';
        } else {
            let matches = false;
            switch(type) {
                case 'sentiment':
                    matches = element.getAttribute('data-sentiment') === value.toLowerCase();
                    break;
                case 'tone':
                    const selectedTones = value.toLowerCase().split(',');
                    const commentTones = element.getAttribute('data-tones').split('|');
                    matches = selectedTones.every(tone => commentTones.includes(tone));
                    break;
                case 'special-flag':
                    const selectedFlags = value.toLowerCase().split(',');
                    const commentFlags = element.getAttribute('data-flags').split('|');
                    matches = selectedFlags.every(flag => commentFlags.includes(flag));
                    break;
            }

            element.style.display = show === matches ? 'block' : 'none';
        }
    });
}

// Function to find and click the cinema mode button
function toggleTheaterMode() {
    const theaterButton = document.querySelector('button.ytp-size-button');
    if (theaterButton) {
        theaterButton.click();
        return true;
    }
    return false;
}

// Function to toggle suggested videos visibility
function toggleSuggestedVideos(show) {
    const relatedContainer = document.getElementById('related');
    if (relatedContainer) {
        relatedContainer.style.display = show ? 'block' : 'none';
        return true;
    }
    return false;
}

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startAnalysis') {
        analyzeComments(message.displayMode, message.transcript);
        sendResponse({received: true});
        return true;
    } else if (message.action === 'filterComments') {
        filterComments(message.filterType, message.value, message.show);
        return true;
    } else if (message.action === 'toggleCinemaMode') {
        const cinemaButton = document.querySelector('.ytp-size-button');
        if (cinemaButton && message.enabled !== document.fullscreenElement) {
            cinemaButton.click();
        }
        return true;
    } else if (message.action === 'toggleSuggestedVideos') {
        const secondary = document.getElementById('secondary');
        if (secondary) {
            secondary.style.display = message.hidden ? 'none' : 'block';
        }
        return true;
    }
});