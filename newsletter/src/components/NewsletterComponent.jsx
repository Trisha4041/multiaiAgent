import { useEffect, useState } from "react";

const NewsletterComponent = () => {
    const [keywords, setKeywords] = useState([]);
    const [newsArticles, setNewsArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchKeywordsFromExtension = async () => {
            try {
                if (window.chrome && chrome.runtime) {
                    chrome.runtime.sendMessage(
                        { action: "getTopKeywords", limit: 5 },
                        (response) => {
                            if (chrome.runtime.lastError) {
                                console.error("Chrome extension error:", chrome.runtime.lastError);
                                setError("Extension communication error");
                            }
                            if (response && response.keywords) {
                                console.log("Received keywords:", response.keywords);
                                setKeywords(response.keywords);
                                fetchNewsForKeywords(response.keywords);
                            } else {
                                console.error("No response received from extension.");
                                setError("Couldn't retrieve keywords from extension");
                            }
                            setLoading(false);
                        }
                    );
                } else {
                    console.warn("Chrome extension not detected.");
                    const mockKeywords = ["technology", "science", "health"];
                    setKeywords(mockKeywords);
                    fetchNewsForKeywords(mockKeywords);
                    setLoading(false);
                }
            } catch (err) {
                console.error("Error connecting to extension:", err);
                setError("Error connecting to extension: " + err.message);
                setLoading(false);
            }
        };

        fetchKeywordsFromExtension();
    }, []);

    const fetchNewsForKeywords = async (keywords) => {
        if (!keywords.length) return;

        const API_KEY = "a942405e87a349179baa3932323063c7"; // Replace with your actual API key
        const BASE_URL = "https://newsapi.org/v2/everything";

        try {
            const query = keywords.join(" OR "); // Join keywords with OR for broader search
            const response = await fetch(`${BASE_URL}?q=${query}&apiKey=${API_KEY}&language=en&sortBy=publishedAt`);
            const data = await response.json();

            if (data.articles) {
                setNewsArticles(data.articles);
                console.log("News fetched successfully:", data.articles);
            } else {
                console.error("No articles found", data);
            }
        } catch (error) {
            console.error("Error fetching news:", error);
        }
    };

    if (loading) return <p className="text-center text-gray-500 text-lg">Loading...</p>;
    if (error) return <p className="text-center text-red-500 font-semibold">{error}</p>;

    return (
        <div className="max-w-7xl mx-auto p-6 bg-gray-100 rounded-lg shadow-lg mt-8">
            <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">📰 Latest News Based on Your Browsing History</h2>

            {newsArticles.length > 0 ? (
                <div className="grid grid-cols-3 gap-6">
                    {newsArticles.map((article, index) => (
                        <div 
                            key={index} 
                            className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition duration-300"
                        >
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                                {article.urlToImage && (
                                    <img src={article.urlToImage} alt={article.title} className="w-full h-48 object-cover rounded-lg" />
                                )}
                                <h3 className="text-lg font-semibold text-gray-800 mt-3">{article.title}</h3>
                            </a>
                            <p className="text-gray-600 text-sm mt-2">{article.description}</p>
                        </div>
                    ))}
                </div>
            ) : (
                <p className="text-center text-gray-500">No news articles found for the selected keywords.</p>
            )}
        </div>
    );
};

export default NewsletterComponent;