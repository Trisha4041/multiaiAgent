import { useState } from "react";
import axios from "axios";

const EmailBot = () => {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [emailHistory, setEmailHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Base URL for API
  const API_BASE_URL = "http://localhost:8000";

  // Clear messages after delay
  const clearMessages = () => {
    setTimeout(() => {
      setErrorMsg("");
      setSuccessMsg("");
    }, 5000);
  };

  // Display status message
  const showMessage = (isError, message) => {
    if (isError) {
      setErrorMsg(message);
      setSuccessMsg("");
    } else {
      setSuccessMsg(message);
      setErrorMsg("");
    }
    clearMessages();
  };

  // Fetch Previous Emails
  const fetchEmails = async () => {
    if (!subject) {
      showMessage(true, "Please enter a subject to fetch email history.");
      return;
    }
    
    setLoading(true);
    setErrorMsg("");
    
    try {
      console.log(`Fetching emails for subject: ${subject}`);
      const response = await axios.get(`${API_BASE_URL}/fetch-emails`, {
        params: { subject: subject }
      });
      
      console.log("Fetch response:", response.data);
      
      const emails = response.data.emails || [];
      setEmailHistory(emails);
      
      if (emails.length > 0) {
        setShowHistory(true);
        showMessage(false, `Found ${emails.length} related emails`);
      } else {
        showMessage(true, "No email history found for this subject.");
      }
    } catch (error) {
      console.error("Error fetching emails:", error);
      
      // Log detailed error information
      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
      }
      
      showMessage(true, `Failed to fetch emails: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Generate AI Email
  const generateEmail = async () => {
    if (!subject) {
      showMessage(true, "Please enter a subject first.");
      return;
    }
    
    setGenerating(true);
    setErrorMsg("");
    
    try {
      // Log the request payload
      const payload = {
        subject,
        email_history: emailHistory
      };
      console.log("Generating email with payload:", payload);
      
      const response = await axios.post(`${API_BASE_URL}/generate-email`, payload);
      
      console.log("Generation response:", response.data);
      
      if (response.data.email_content) {
        setEmailBody(response.data.email_content);
        showMessage(false, "Email generated successfully!");
      } else {
        showMessage(true, "Generated email was empty. Please try again.");
      }
    } catch (error) {
      console.error("Error generating email:", error);
      
      // Log detailed error information
      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
      } else if (error.request) {
        console.error("No response received:", error.request);
      } else {
        console.error("Error setting up request:", error.message);
      }
      
      showMessage(true, `Failed to generate email: ${error.response?.data?.detail || error.message}`);
    } finally {
      setGenerating(false);
    }
  };

  // Send Email
  const sendEmail = async () => {
    if (!recipient || !subject || !emailBody) {
      showMessage(true, "Please fill in all fields before sending.");
      return;
    }
    
    setSending(true);
    setErrorMsg("");
    
    try {
      // Log the request payload
      const payload = {
        to: recipient,
        subject,
        body: emailBody
      };
      console.log("Sending email with payload:", payload);
      
      const response = await axios.post(`${API_BASE_URL}/send-email`, payload);
      
      console.log("Send response:", response.data);
      
      showMessage(false, "✅ Email sent successfully!");
      // Clear form after successful send
      setEmailBody("");
    } catch (error) {
      console.error("Error sending email:", error);
      
      // Log detailed error information
      if (error.response) {
        console.error("Response data:", error.response.data);
        console.error("Response status:", error.response.status);
      }
      
      showMessage(true, `Failed to send email: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSending(false);
    }
  };

  // Test backend connection
  const testConnection = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/debug/config`);
      console.log("API configuration:", response.data);
      showMessage(false, "Connected to backend successfully");
    } catch (error) {
      console.error("Connection test failed:", error);
      showMessage(true, `Backend connection failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-gray-100 shadow-lg rounded-lg mt-10 border border-gray-300">
      <h2 className="text-2xl font-bold text-center text-gray-800 mb-4">📧 AI Email Assistant</h2>
      
      {/* Status Messages */}
      {errorMsg && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 rounded">
          <p>{errorMsg}</p>
        </div>
      )}
      
      {successMsg && (
        <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4 rounded">
          <p>{successMsg}</p>
        </div>
      )}
      
      <input
        type="email"
        placeholder="Recipient Email"
        value={recipient}
        onChange={(e) => setRecipient(e.target.value)}
        className="w-full p-3 border border-gray-400 bg-white rounded-md mb-3 text-gray-900 placeholder-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      
      <input
        type="text"
        placeholder="Email Subject"
        value={subject}
        onChange={(e) => setSubject(e.target.value)}
        className="w-full p-3 border border-gray-400 bg-white rounded-md mb-3 text-gray-900 placeholder-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      
      <div className="flex flex-col space-y-3 mb-4">
        <div className="flex space-x-2">
          <button 
            onClick={fetchEmails} 
            disabled={loading}
            className="flex-1 bg-blue-600 text-white p-3 rounded hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {loading ? "Fetching..." : "🔍 Fetch Email History"}
          </button>
          
          <button
            onClick={testConnection}
            disabled={loading}
            className="bg-gray-600 text-white px-3 rounded hover:bg-gray-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            title="Test backend connection"
          >
            🔄
          </button>
        </div>
        
        <button 
          onClick={generateEmail} 
          disabled={generating}
          className="w-full bg-green-600 text-white p-3 rounded hover:bg-green-700 transition disabled:bg-green-400 disabled:cursor-not-allowed"
        >
          {generating ? "Generating..." : "🤖 Generate Email"}
        </button>
      </div>
      
      {/* Email History Section */}
      {showHistory && (
        <div className="mb-4 border border-gray-300 rounded-md p-3 bg-white">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-bold">Email History ({emailHistory.length})</h3>
            <button 
              onClick={() => setShowHistory(false)} 
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Hide
            </button>
          </div>
          
          {emailHistory.length > 0 ? (
            <div className="max-h-40 overflow-y-auto text-sm text-gray-700">
              {emailHistory.map((snippet, index) => (
                <div key={index} className="mb-2 p-2 border-b border-gray-200">
                  {snippet}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No email history found</p>
          )}
        </div>
      )}
      
      {/* Email Body Textarea */}
      <textarea
        placeholder="Email Body (generated or write your own)"
        value={emailBody}
        onChange={(e) => setEmailBody(e.target.value)}
        rows={8}
        className="w-full p-3 border border-gray-400 bg-white rounded-md mb-3 text-gray-900 placeholder-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      
      <button 
        onClick={sendEmail} 
        disabled={sending}
        className="w-full bg-purple-600 text-white p-3 rounded hover:bg-purple-700 transition disabled:bg-purple-400 disabled:cursor-not-allowed"
      >
        {sending ? "Sending..." : "📤 Send Email"}
      </button>
      
      <div className="mt-4 text-xs text-gray-500 text-center">
        <p>Version 1.0.2 • Connected to API at {API_BASE_URL}</p>
      </div>
    </div>
  );
};

export default EmailBot;