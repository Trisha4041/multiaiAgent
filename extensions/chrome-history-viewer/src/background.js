chrome.runtime.onInstalled.addListener(() => {
    console.log("Chrome History Viewer Extension Installed");
});

// Listen for messages from React app
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getTopKeywords") {
        fetchTopKeywords(request.limit).then((keywords) => {
            sendResponse({ keywords });
        });
        return true; // Keep the message channel open for async response
    }
});

// Function to fetch top keywords from browsing history
async function fetchTopKeywords(limit = 5) {
    return new Promise((resolve) => {
        chrome.history.search({ text: "", maxResults: 1000 }, (historyItems) => {
            const keywordCount = {};

            historyItems.forEach((item) => {
                const words = item.title ? item.title.split(/\s+/) : [];
                words.forEach((word) => {
                    const cleanedWord = word.toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
                    if (cleanedWord.length > 3) {
                        keywordCount[cleanedWord] = (keywordCount[cleanedWord] || 0) + 1;
                    }
                });
            });

            const sortedKeywords = Object.entries(keywordCount)
                .sort((a, b) => b[1] - a[1])
                .slice(0, limit)
                .map(([word]) => word);

            resolve(sortedKeywords);
        });
    });
}
