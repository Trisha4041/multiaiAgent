import os
import base64
import json
import requests
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Ensure API Key is set
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    logger.error("Together AI API key is missing. Set it in your environment variables.")
    raise RuntimeError("Together AI API key is missing. Set it in your environment variables.")

# Authenticate Gmail API
try:
    creds = Credentials.from_authorized_user_file(
        "token.json",
        scopes=["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]
    )
    gmail_service = build("gmail", "v1", credentials=creds)
    logger.info("Gmail API authentication successful")
except Exception as e:
    logger.error(f"Failed to authenticate Gmail API: {e}")
    raise RuntimeError(f"Failed to authenticate Gmail API: {e}")

# FastAPI App
app = FastAPI(title="Email Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: Optional[str] = None

class GenerateEmailRequest(BaseModel):
    subject: str
    email_history: Optional[List[str]] = []

# Global error handler
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

# Handle favicon request to avoid 404 logs
@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon"}

# Simple HTML form for generating emails (for browser testing)
@app.get("/", response_class=HTMLResponse)
async def get_root():
    return """
    <html>
        <head>
            <title>Email Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
                form { display: flex; flex-direction: column; }
                label { margin-top: 10px; }
                input, textarea { padding: 8px; margin-bottom: 10px; }
                button { padding: 10px; background: #4285f4; color: white; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <h1>Email Assistant</h1>
            <form action="/generate-email-form" method="post">
                <label for="to">To:</label>
                <input type="email" id="to" name="to" required>
                
                <label for="subject">Subject:</label>
                <input type="text" id="subject" name="subject" required>
                
                <button type="submit">Generate Email</button>
            </form>
            
            <h2>Send Custom Email</h2>
            <form action="/send-email-form" method="post">
                <label for="to">To:</label>
                <input type="email" id="to" name="to" required>
                
                <label for="subject">Subject:</label>
                <input type="text" id="subject" name="subject" required>
                
                <label for="body">Body:</label>
                <textarea id="body" name="body" rows="10" required></textarea>
                
                <button type="submit">Send Email</button>
            </form>
        </body>
    </html>
    """

# Fetch previous emails
def get_email_history(subject: str):
    try:
        logger.info(f"Fetching email history for subject: {subject}")
        response = gmail_service.users().messages().list(userId="me", q=f"subject:{subject}", maxResults=10).execute()
        messages = response.get("messages", [])
        
        if not messages:
            logger.info("No previous email history found")
            return []

        email_threads = []
        for msg in messages:
            email_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            snippet = email_data.get("snippet", "")
            email_threads.append(snippet)

        logger.info(f"Found {len(email_threads)} emails in history")
        return email_threads
    except Exception as e:
        logger.error(f"Failed to fetch email history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch email history: {e}")

# API endpoint for fetching emails
@app.get("/fetch-emails")
def fetch_emails(subject: str = Query(...)):
    try:
        history = get_email_history(subject)
        return {"emails": history}
    except Exception as e:
        logger.error(f"Error in fetch_emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Generate AI-powered email - API endpoint (POST)
@app.post("/generate-email")
def generate_email(request: GenerateEmailRequest):
    logger.info(f"Generating email for subject: {request.subject}")
    
    # Use provided email history or fetch it if empty
    email_history = request.email_history
    if not email_history:
        logger.info("No email history provided, fetching from Gmail...")
        email_history = get_email_history(request.subject)
    
    # Format history for prompt
    history_text = "\n".join(email_history) if email_history else "No previous email history."
    
    # Alternative models if Mistral fails:
    # - "meta-llama/Llama-2-7b-chat-hf"
    # - "gpt-3.5-turbo" (if using OpenAI)
    
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": "You are an AI email assistant."},
            {"role": "user", "content": f"Based on this email history:\n{history_text}\nGenerate a professional email for subject: '{request.subject}'"}
        ],
        "max_tokens": 200
    }
    
    try:
        # Log request details for debugging
        logger.info(f"Sending request to Together AI with subject: {request.subject}")
        logger.info(f"Model being used: {payload['model']}")
        
        response = requests.post(api_url, json=payload, headers=headers)
        
        logger.info(f"Together AI response status: {response.status_code}")
        
        # Check for non-200 status
        if response.status_code != 200:
            logger.error(f"Together AI error: {response.text}")
            # Try to return message from JSON if available
            try:
                error_json = response.json()
                error_message = error_json.get('error', {}).get('message', response.text)
                raise HTTPException(status_code=response.status_code, detail=f"AI API error: {error_message}")
            except json.JSONDecodeError:
                # If not JSON, return text
                raise HTTPException(status_code=response.status_code, detail=f"AI API error: {response.text}")
        
        # Try to parse response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {response.text[:500]}")
            raise HTTPException(status_code=500, detail="AI API returned invalid JSON")
        
        # Check for expected data structure
        if "choices" in data and data["choices"] and len(data["choices"]) > 0:
            if "message" in data["choices"][0] and "content" in data["choices"][0]["message"]:
                generated_email = data["choices"][0]["message"]["content"].strip()
                logger.info("Email generated successfully")
                return {"email_content": generated_email}
            else:
                logger.error(f"Unexpected response structure: {data}")
                raise HTTPException(status_code=500, detail="AI API response missing expected fields")
        else:
            logger.error(f"API response missing choices: {data}")
            raise HTTPException(status_code=500, detail="API response missing choices")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"AI API request failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in generate_email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Generate email - Form version (works with HTML form)
@app.post("/generate-email-form", response_class=HTMLResponse)
async def generate_email_form(to: str = Form(...), subject: str = Form(...)):
    try:
        # Reuse the email generation logic
        request = GenerateEmailRequest(subject=subject)
        result = generate_email(request)
        
        generated_email = result["email_content"]
        
        # Return HTML form with generated email
        return f"""
        <html>
            <head>
                <title>Generated Email</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    form {{ display: flex; flex-direction: column; }}
                    label {{ margin-top: 10px; }}
                    input, textarea {{ padding: 8px; margin-bottom: 10px; }}
                    button {{ padding: 10px; background: #4285f4; color: white; border: none; cursor: pointer; }}
                </style>
            </head>
            <body>
                <h1>Generated Email</h1>
                <form action="/send-email-form" method="post">
                    <label for="to">To:</label>
                    <input type="email" id="to" name="to" value="{to}" required>
                    
                    <label for="subject">Subject:</label>
                    <input type="text" id="subject" name="subject" value="{subject}" required>
                    
                    <label for="body">Body:</label>
                    <textarea id="body" name="body" rows="10" required>{generated_email}</textarea>
                    
                    <button type="submit">Send Email</button>
                </form>
                <p><a href="/">Back to form</a></p>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in generate_email_form: {e}")
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>Failed to generate email: {str(e)}</p>
                <p><a href="/">Back to form</a></p>
            </body>
        </html>
        """

# Send email - API endpoint (POST)
@app.post("/send-email")
def send_email(request: EmailRequest):
    logger.info(f"Sending email to: {request.to} with subject: {request.subject}")
    
    if not request.body:
        logger.error("Email body is missing")
        raise HTTPException(status_code=400, detail="Email body is required")
    
    try:
        message = MIMEText(request.body)
        message["to"] = request.to
        message["subject"] = request.subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        logger.info("Email sent successfully")
        return {"status": "Email sent successfully!"}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

# Send email - Form version (works with HTML form)
@app.post("/send-email-form", response_class=HTMLResponse)
async def send_email_form(to: str = Form(...), subject: str = Form(...), body: str = Form(...)):
    try:
        request = EmailRequest(to=to, subject=subject, body=body)
        result = send_email(request)
        
        return f"""
        <html>
            <head>
                <title>Email Sent</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                </style>
            </head>
            <body>
                <h1>Success!</h1>
                <p>{result['status']}</p>
                <p>Email was sent to: {to}</p>
                <p>Subject: {subject}</p>
                <p><a href="/">Back to form</a></p>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error in send_email_form: {e}")
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>Failed to send email: {str(e)}</p>
                <p><a href="/">Back to form</a></p>
            </body>
        </html>
        """

# Debug endpoint - Check configuration
@app.get("/debug/config")
def debug_config():
    return {
        "api_key_set": bool(TOGETHER_API_KEY),
        "gmail_authenticated": bool(gmail_service),
        "models_available": ["mistralai/Mistral-7B-Instruct-v0.1", "meta-llama/Llama-2-7b-chat-hf"]
    }

# Testing endpoint - Test AI without Gmail
@app.post("/debug/test-ai")
def test_ai(message: str = "Generate a short test email"):
    api_url = "https://api.together.xyz/v1/chat/completions"
    headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/Llama-2-7b-chat-hf",  # Alternative model as a fallback
        "messages": [
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": message}
        ],
        "max_tokens": 100
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Test AI failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)