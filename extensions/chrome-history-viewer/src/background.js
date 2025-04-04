const commonWords = [
    "the", "and", "for", "that", "this", "with", "from", "your", "what", "have", 
    "you", "are", "com", "org", "net", "www", "http", "https", "html", "page", 
    "site", "web", "home", "not", "can", "all", "get", "has", "will", "about"
];

chrome.runtime.onInstalled.addListener(() => {
    console.log("Chrome History Explorer Extension Installed");
    chrome.storage.sync.set({
        historyRetentionDays: 7,
        autoExport: false
    });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getTopKeywords") {
        getTopKeywords(request.days || 7)
            .then(keywords => sendResponse({ keywords }))
            .catch(error => {
                console.error("Keyword extraction failed:", error);
                sendResponse({ keywords: [] });
            });
        return true;
    }

    if (request.action === "getDailyUsage") {
        getDailyUsage(request.days || 7)
            .then(dailyUsage => sendResponse({ dailyUsage }))
            .catch(error => {
                console.error("Daily usage calculation failed:", error);
                sendResponse({ dailyUsage: [] });
            });
        return true;
    }

    return true;
});

async function getTopKeywords(days) {
    const historyItems = await searchHistory(days, 1000);
    
    const words = {};
    historyItems.forEach(item => {
        if (item.title) {
            item.title
                .toLowerCase()
                .split(/\s+/)
                .filter(word => word.length > 3 && !commonWords.includes(word))
                .forEach(word => {
                    words[word] = (words[word] || 0) + 1;
                });
        }
    });

    return Object.entries(words)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([word]) => word);
}

async function getDailyUsage(days) {
    const historyItems = await searchHistory(days, 1000);
    const millisecondsPerDay = 24 * 60 * 60 * 1000;
    const dailyData = {};

    for (let i = 0; i < days; i++) {
        const date = new Date(Date.now() - (i * millisecondsPerDay));
        const dateStr = date.toISOString().split("T")[0]; // Format YYYY-MM-DD
        dailyData[dateStr] = { visits: 0, uniqueSites: new Set(), timeSpent: 0 };
    }

    historyItems.forEach(item => {
        if (!item.lastVisitTime) return; // Skip if missing lastVisitTime

        const visitDate = new Date(item.lastVisitTime);
        const dateStr = visitDate.toISOString().split("T")[0];

        if (dailyData[dateStr]) {
            dailyData[dateStr].visits += 1;
            try {
                const domain = new URL(item.url).hostname;
                dailyData[dateStr].uniqueSites.add(domain);
            } catch (e) {
                console.warn("Invalid URL:", item.url);
            }
            dailyData[dateStr].timeSpent += 2; // Estimate: 2 minutes per page
        }
    });

    return Object.entries(dailyData).map(([name, data]) => ({
        name,
        timeSpent: data.timeSpent,
        visits: data.visits,
        uniqueSites: data.uniqueSites.size
    }));
}

function searchHistory(days, maxResults = 1000) {
    return new Promise((resolve, reject) => {
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        const startTime = Date.now() - (days * millisecondsPerDay);

        chrome.history.search(
            { text: "", startTime, maxResults, endTime: Date.now() },
            (items) => {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else {
                    resolve(items);
                }
            }
        );
    });
}
