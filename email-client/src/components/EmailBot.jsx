// ... imports stay the same
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box, Card, CardContent, Typography, List, ListItem, ListItemText,
  Button, CircularProgress, Alert, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Snackbar
} from '@mui/material';

const API_BASE_URL = 'http://localhost:8000';

const EmailBot = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [composeOpen, setComposeOpen] = useState(false);
  const [newEmail, setNewEmail] = useState({ to: '', subject: '', body: '' });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [loadingAI, setLoadingAI] = useState(false);

  useEffect(() => {
    fetchUnreadEmails();
  }, []);

  const fetchUnreadEmails = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/unread-emails`, { timeout: 60000 });
      setEmails(response.data.emails || []);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch emails';
      setError(`Unable to fetch emails: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      await axios.post(`${API_BASE_URL}/mark-as-read`, { message_id: messageId });
      setEmails(emails.filter(email => email.id !== messageId));
      showSnackbar('Email marked as read', 'success');
    } catch {
      showSnackbar('Failed to mark email as read', 'error');
    }
  };

  const sendEmail = async () => {
    try {
      await axios.post(`${API_BASE_URL}/send-email`, newEmail);
      setComposeOpen(false);
      resetComposeForm();
      showSnackbar('Email sent successfully', 'success');
    } catch {
      showSnackbar('Failed to send email', 'error');
    }
  };

  const createEventFromEmail = async (email) => {
    if (!email.potentialDates?.length) {
      showSnackbar('No dates found in this email', 'warning');
      return;
    }

    try {
      const dateString = email.potentialDates[0];
      const eventDate = new Date(dateString);
      if (isNaN(eventDate.getTime())) {
        showSnackbar('Invalid date format', 'error');
        return;
      }

      const endDate = new Date(eventDate);
      endDate.setHours(endDate.getHours() + 1);

      await axios.post(`${API_BASE_URL}/create-event`, {
        summary: `Meeting regarding: ${email.subject}`,
        description: `From email from ${email.from}\n\n${email.snippet}`,
        start_datetime: eventDate.toISOString(),
        end_datetime: endDate.toISOString(),
        attendees: [email.from.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/)?.[0]]
      });

      showSnackbar('Calendar event created', 'success');
    } catch {
      showSnackbar('Failed to create calendar event', 'error');
    }
  };

  const generateWithAI = async () => {
    if (!newEmail.subject) {
      showSnackbar('Please enter a subject to generate the email', 'warning');
      return;
    }

    try {
      setLoadingAI(true);
      const response = await axios.post(`${API_BASE_URL}/generate-email`, {
        subject: newEmail.subject
      });
      const generated = response.data.email_content || 'Generated content not available.';

      setNewEmail(prev => ({ ...prev, body: generated }));
      showSnackbar('Email body generated!', 'success');
    } catch (err) {
      console.error('AI generation failed:', err);
      showSnackbar('Failed to generate email body', 'error');
    } finally {
      setLoadingAI(false);
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const resetComposeForm = () => {
    setNewEmail({ to: '', subject: '', body: '' });
  };

  const handleComposeChange = (e) => {
    const { name, value } = e.target;
    setNewEmail(prev => ({ ...prev, [name]: value }));
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>Email Assistant</Typography>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Button variant="contained" onClick={fetchUnreadEmails} disabled={loading}>Refresh Emails</Button>
        <Button variant="outlined" onClick={() => setComposeOpen(true)}>Compose Email</Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Unread Emails</Typography>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}><CircularProgress /></Box>
          ) : emails.length === 0 ? (
            <Typography variant="body1" color="textSecondary" align="center">No unread emails found</Typography>
          ) : (
            <List>
              {emails.map((email) => (
                <ListItem key={email.id} divider sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' } }} onClick={() => setSelectedEmail(email)}>
                  <ListItemText
                    primary={<Typography variant="subtitle1" noWrap>{email.subject}</Typography>}
                    secondary={
                      <>
                        <Typography variant="body2" color="textSecondary">From: {email.from}</Typography>
                        <Typography variant="body2" color="textSecondary">{new Date(email.date).toLocaleString()}</Typography>
                        <Typography variant="body2" noWrap>{email.snippet}</Typography>
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* View Email Dialog */}
      <Dialog open={Boolean(selectedEmail)} onClose={() => setSelectedEmail(null)} maxWidth="md" fullWidth>
        {selectedEmail && (
          <>
            <DialogTitle>{selectedEmail.subject}</DialogTitle>
            <DialogContent>
              <Typography variant="body2" color="textSecondary"><strong>From:</strong> {selectedEmail.from}</Typography>
              <Typography variant="body2" color="textSecondary"><strong>Date:</strong> {new Date(selectedEmail.date).toLocaleString()}</Typography>
              <Typography variant="body1" paragraph>{selectedEmail.snippet}</Typography>

              {selectedEmail.potentialDates?.length > 0 && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0, 0, 0, 0.04)', borderRadius: 1 }}>
                  <Typography variant="subtitle2">Potential dates mentioned:</Typography>
                  <List dense>
                    {selectedEmail.potentialDates.map((date, index) => (
                      <ListItem key={index}><ListItemText primary={date} /></ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => createEventFromEmail(selectedEmail)}>Create Calendar Event</Button>
              <Button onClick={() => markAsRead(selectedEmail.id)}>Mark as Read</Button>
              <Button onClick={() => setSelectedEmail(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Compose Email Dialog */}
      <Dialog open={composeOpen} onClose={() => setComposeOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Compose Email</DialogTitle>
        <DialogContent>
          <TextField margin="dense" label="To" type="email" fullWidth name="to" value={newEmail.to} onChange={handleComposeChange} sx={{ mb: 2 }} />
          <TextField margin="dense" label="Subject" fullWidth name="subject" value={newEmail.subject} onChange={handleComposeChange} sx={{ mb: 2 }} />
          <TextField margin="dense" label="Body" multiline rows={8} fullWidth name="body" value={newEmail.body} onChange={handleComposeChange} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComposeOpen(false)}>Cancel</Button>
          <Button onClick={generateWithAI} disabled={loadingAI}>
            {loadingAI ? 'Generating...' : 'Generate with AI'}
          </Button>
          <Button onClick={sendEmail} color="primary" variant="contained">Send</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EmailBot;