document.addEventListener('DOMContentLoaded', () => {
    const historyList = document.getElementById('history-list');
    const timeRangeSelect = document.getElementById('time-range');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const exportCsvBtn = document.getElementById('export-csv');
    const clearFiltersBtn = document.getElementById('clear-filters');

    function fetchHistory(timeRange, searchTerm = '') {
        const millisecondsPerDay = 24 * 60 * 60 * 1000;
        const startTime = Date.now() - (timeRange * millisecondsPerDay);

        chrome.history.search({
            text: searchTerm,
            startTime: startTime,
            maxResults: 500
        }, (historyItems) => {
            displayHistory(historyItems);
        });
    }

    function displayHistory(historyItems) {
        // Clear the history list using DOM methods instead of innerHTML
        while (historyList.firstChild) {
            historyList.removeChild(historyList.firstChild);
        }
        
        historyItems.sort((a, b) => b.lastVisitTime - a.lastVisitTime);
        
        historyItems.forEach(item => {
            const historyItemDiv = document.createElement('div');
            historyItemDiv.classList.add('history-item');
            
            const title = document.createElement('strong');
            title.textContent = item.title || 'Untitled';
            
            const lineBreak1 = document.createElement('br');
            
            const dateSmall = document.createElement('small');
            const visitDate = new Date(item.lastVisitTime);
            dateSmall.textContent = visitDate.toLocaleString();
            
            const lineBreak2 = document.createElement('br');
            
            const link = document.createElement('a');
            link.href = item.url;
            link.target = '_blank';
            link.textContent = item.url;
            
            historyItemDiv.appendChild(title);
            historyItemDiv.appendChild(lineBreak1);
            historyItemDiv.appendChild(dateSmall);
            historyItemDiv.appendChild(lineBreak2);
            historyItemDiv.appendChild(link);
            
            historyList.appendChild(historyItemDiv);
        });
    }

    timeRangeSelect.addEventListener('change', () => {
        fetchHistory(parseInt(timeRangeSelect.value));
    });

    searchBtn.addEventListener('click', () => {
        fetchHistory(parseInt(timeRangeSelect.value), searchInput.value.trim());
    });

    // Add enter key support for search
    searchInput.addEventListener('keyup', (event) => {
        if (event.key === 'Enter') {
            fetchHistory(parseInt(timeRangeSelect.value), searchInput.value.trim());
        }
    });

    exportCsvBtn.addEventListener('click', () => {
        chrome.history.search({
            text: '',
            startTime: Date.now() - (parseInt(timeRangeSelect.value) * 24 * 60 * 60 * 1000),
            maxResults: 1000
        }, (historyItems) => {
            const csvContent = convertToCSV(historyItems);
            downloadCSV(csvContent);
        });
    });

    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        timeRangeSelect.value = '7';
        fetchHistory(7);
    });

    function convertToCSV(historyItems) {
        const headers = ['Title', 'URL', 'Visit Time'];
        const rows = historyItems.map(item => {
            // Safely handle null/undefined title
            const title = (item.title || 'Untitled').replace(/"/g, '""');
            return [
                `"${title}"`,
                `"${item.url}"`,
                `"${new Date(item.lastVisitTime).toLocaleString()}"`
            ];
        });
        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    function downloadCSV(csvContent) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `chrome_history_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);
    }

    // Initialize with 7-day history
    fetchHistory(7);
});