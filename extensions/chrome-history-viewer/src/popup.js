document.addEventListener('DOMContentLoaded', () => {
    const historyList = document.getElementById('history-list');
    const timeRangeSelect = document.getElementById('time-range');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const exportCsvBtn = document.getElementById('export-csv');
    const clearFiltersBtn = document.getElementById('clear-filters');

    // Fetch history items based on time range & search term
    async function fetchHistory(timeRange, searchTerm = '') {
        try {
            const millisecondsPerDay = 24 * 60 * 60 * 1000;
            const startTime = Date.now() - (timeRange * millisecondsPerDay);

            chrome.history.search(
                { text: searchTerm, startTime, maxResults: 500 },
                (historyItems) => {
                    if (chrome.runtime.lastError) {
                        console.error("Error fetching history:", chrome.runtime.lastError);
                        return;
                    }
                    displayHistory(historyItems);
                }
            );
        } catch (error) {
            console.error("Fetch history failed:", error);
        }
    }

    // Display history in the popup
    function displayHistory(historyItems) {
        historyList.innerHTML = ''; // Clear previous results

        if (historyItems.length === 0) {
            historyList.innerHTML = "<p>No history found.</p>";
            return;
        }

        const fragment = document.createDocumentFragment(); // Improve performance
        historyItems.sort((a, b) => b.lastVisitTime - a.lastVisitTime);

        historyItems.forEach(item => {
            const historyItemDiv = document.createElement('div');
            historyItemDiv.classList.add('history-item');

            const visitDate = new Date(item.lastVisitTime).toLocaleString();
            historyItemDiv.innerHTML = `
                <strong>${item.title || 'Untitled'}</strong><br>
                <small>${visitDate}</small><br>
                <a href="${item.url}" target="_blank">${item.url}</a>
            `;

            fragment.appendChild(historyItemDiv);
        });

        historyList.appendChild(fragment);
    }

    // Convert history items to CSV format
    function convertToCSV(historyItems) {
        const headers = ['Title', 'URL', 'Visit Time'];
        const rows = historyItems.map(item => [
            `"${item.title?.replace(/"/g, '""') || 'Untitled'}"`,
            `"${item.url}"`,
            `"${new Date(item.lastVisitTime).toLocaleString()}"`
        ]);

        return [headers, ...rows]
            .map(row => row.join(','))
            .join('\n');
    }

    // Download CSV file
    function downloadCSV(csvContent) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `chrome_history_${new Date().toISOString().split('T')[0]}.csv`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Event Listeners
    timeRangeSelect.addEventListener('change', () => {
        fetchHistory(parseInt(timeRangeSelect.value));
    });

    searchBtn.addEventListener('click', () => {
        fetchHistory(parseInt(timeRangeSelect.value), searchInput.value.trim());
    });

    exportCsvBtn.addEventListener('click', () => {
        chrome.history.search(
            { text: '', startTime: Date.now() - (parseInt(timeRangeSelect.value) * 24 * 60 * 60 * 1000), maxResults: 1000 },
            (historyItems) => downloadCSV(convertToCSV(historyItems))
        );
    });

    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        timeRangeSelect.value = '7';
        fetchHistory(7);
    });

    // Initial history load
    fetchHistory(7);
});
