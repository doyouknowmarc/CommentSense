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
        observer.disconnect();  // Stop observing once title is found
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
        .map(element => {
            let fullText = '';
            
            // Recursive function to process nodes and their children
            function processNode(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    fullText += node.textContent;
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                    if (node.tagName === 'IMG') {
                        // Direct emoji image
                        fullText += node.alt;
                    } else {
                        // Process all child nodes
                        node.childNodes.forEach(processNode);
                    }
                }
            }

            // Process the entire comment element
            element.childNodes.forEach(processNode);
            return fullText.trim();
        })
        .filter(comment => comment !== '');

    return { 
        comments, 
        commentElements: Array.from(document.querySelectorAll('ytd-comment-thread-renderer'))
            .filter((_, i) => comments[i] !== '') 
    };
}

// Function to create a sentiment tag
function createSentimentTag(sentiment, modelType, reasoning, model, confidence) {
    const colors = {
        'POSITIVE': '#e6ffe6',
        'NEUTRAL': '#f0f0f0',
        'NEGATIVE': '#ffe6e6'
    };
    
    const tag = document.createElement('div');
    tag.className = 'sentiment-tag';
    tag.style.cssText = `
        display: inline-block;
        padding: 4px 8px;
        margin: 4px 0;
        border-radius: 4px;
        cursor: pointer;
        background-color: ${colors[sentiment] || '#ffffff'};
        border: 1px solid #ddd;
        font-size: 12px;
        transition: all 0.3s ease;
    `;
    
    let detailsText = '';
    if (modelType === 'bert' && confidence !== undefined) {
        detailsText = `Confidence: ${(confidence * 100).toFixed(2)}%`;
    } else if (modelType === 'llama' && reasoning && model) {
        detailsText = `${model}: ${reasoning}`;
    }
    
    tag.textContent = sentiment;
    tag.setAttribute('data-details', detailsText);
    tag.addEventListener('click', () => {
        tag.textContent = tag.textContent === sentiment ? detailsText : sentiment;
    });
    
    return tag;
}

// Function to highlight comment based on sentiment
function highlightComment(commentElement, sentiment, modelType, reasoning, model, confidence) {
    const colors = {
        'POSITIVE': '#e6ffe6',
        'NEUTRAL': '#f0f0f0',
        'NEGATIVE': '#ffe6e6'
    };
    commentElement.style.backgroundColor = colors[sentiment] || '#ffffff';
    commentElement.setAttribute('data-sentiment', sentiment.toLowerCase());

    // Find the comment content element
    const commentContent = commentElement.querySelector('#content #content-text');
    if (!commentContent) return;

    // Create and style info container
    const infoContainer = document.createElement('div');
    infoContainer.style.cssText = 'margin-top: 8px; padding: 8px; font-size: 12px; color: #666;';

    // Create sentiment tag
    const tag = createSentimentTag(
        sentiment,
        modelType,
        reasoning,
        modelType === 'llama' ? 'mistral-small:22b' : null,
        confidence
    );

    // Add sentiment text and tag
    const sentimentText = `<strong>Sentiment:</strong> ${sentiment}<br>`;

    if (modelType === 'bert' && confidence !== undefined) {
        // Display confidence score for BERT
        infoContainer.innerHTML = sentimentText + `<strong>Confidence Score:</strong> ${(confidence * 100).toFixed(2)}%`;
    } else if (modelType === 'llama' && reasoning && model) {
        // Display reasoning and model for Small Language Model
        infoContainer.innerHTML = sentimentText + `<strong>AI Model:</strong> ${model}<br><strong>Reasoning:</strong> ${reasoning}`;
    }

    // Insert tag after the comment content
    commentContent.parentNode.insertBefore(tag, commentContent.nextSibling);
    // Append info container after the tag
    commentContent.parentNode.insertBefore(infoContainer, tag.nextSibling);
}

// Function to analyze comments
async function analyzeComments(modelType, displayMode = 'tag', transcript = null) {
    try {
        const { comments, commentElements } = scrapeComments();
        console.log('Scraped comments:', comments);
        if (comments.length === 0) {
            throw new Error('No comments found');
        }

        // Get video ID
        const url = new URL(window.location.href);
        const videoId = url.searchParams.get('v');

        const stats = {
            total: comments.length,
            positive: 0,
            neutral: 0,
            negative: 0
        };

        for (let i = 0; i < comments.length; i++) {
            try {
                const response = await new Promise((resolve, reject) => {
                    chrome.runtime.sendMessage({
                        action: 'analyzeComment',
                        comment: comments[i],
                        modelType: modelType,
                        model: modelType === 'llama' ? 'mistral-small:22b' : null,
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

                // Update stats based on sentiment
                switch(response.sentiment) {
                    case 'POSITIVE': stats.positive++; break;
                    case 'NEUTRAL': stats.neutral++; break;
                    case 'NEGATIVE': stats.negative++; break;
                }
                
                if (displayMode === 'tag') {
                    const tag = createSentimentTag(
                        response.sentiment,
                        modelType,
                        response.reasoning,
                        modelType === 'llama' ? 'mistral-small:22b' : null,
                        response.confidence
                    );
                    commentElements[i].insertBefore(tag, commentElements[i].firstChild);
                    commentElements[i].setAttribute('data-sentiment', response.sentiment.toLowerCase());
                } else {
                    highlightComment(
                        commentElements[i],
                        response.sentiment,
                        modelType,
                        response.reasoning,
                        modelType === 'llama' ? 'mistral-small:22b' : null,
                        response.confidence
                    );
                }
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

// Function to filter comments by sentiment with dynamic loading support
function filterComments(sentiment, show) {
    const commentElements = document.querySelectorAll('ytd-comment-thread-renderer');
    commentElements.forEach(element => {
        const bgColor = element.style.backgroundColor;
        const dataSentiment = element.getAttribute('data-sentiment');
        
        let elementSentiment = '';
        
        // Check both background color and data-sentiment attribute
        if (dataSentiment) {
            elementSentiment = dataSentiment;
        } else {
            elementSentiment = 
                bgColor === 'rgb(230, 255, 230)' || bgColor === '#e6ffe6' ? 'positive' :
                bgColor === 'rgb(240, 240, 240)' || bgColor === '#f0f0f0' ? 'neutral' :
                bgColor === 'rgb(255, 230, 230)' || bgColor === '#ffe6e6' ? 'negative' : '';
        }
        
        if (sentiment === 'all') {
            element.style.display = 'block';
        } else if (elementSentiment && elementSentiment.toLowerCase() === sentiment.toLowerCase()) {
            element.style.display = show ? 'block' : 'none';
        } else {
            element.style.display = show ? 'none' : 'block';
        }
    });
}

// Listen for analysis requests and handle display modes
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startAnalysis') {
        analyzeComments(message.modelType, message.displayMode, message.transcript);
        sendResponse({received: true});
        return true;
    } else if (message.action === 'filterComments') {
        filterComments(message.sentiment, message.show);
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