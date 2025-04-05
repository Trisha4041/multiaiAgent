import React, { useEffect, useState } from 'react';
import axios from 'axios';

const CalendarManager = () => {
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/events');
      const fetchedEvents = response.data?.events;
      if (Array.isArray(fetchedEvents)) {
        setEvents(fetchedEvents);
      } else {
        console.error("Unexpected response structure:", response.data);
        setEvents([]);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const createEvent = async () => {
    try {
      await axios.post('http://localhost:8000/events', {
        summary,
        start,
        end
      });
      setSummary('');
      setStart('');
      setEnd('');
      fetchEvents();
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  const styles = {
    container: {
      backgroundColor: '#0d0d0d',
      color: '#f0f0f0',
      minHeight: '100vh',
      padding: '2rem',
      fontFamily: 'sans-serif',
    },
    heading: {
      fontSize: '2rem',
      marginBottom: '1rem',
      textShadow: '0 0 10px #00ffe1',
    },
    input: {
      backgroundColor: '#1a1a1a',
      border: '1px solid #00ffe1',
      color: '#f0f0f0',
      padding: '0.5rem',
      marginRight: '0.5rem',
      borderRadius: '5px',
      boxShadow: '0 0 5px #00ffe1',
    },
    button: {
      backgroundColor: '#00ffe1',
      color: '#0d0d0d',
      padding: '0.5rem 1rem',
      border: 'none',
      borderRadius: '5px',
      cursor: 'pointer',
      boxShadow: '0 0 10px #00ffe1',
      transition: 'background-color 0.3s ease',
    },
    eventCard: {
      backgroundColor: '#1a1a1a',
      border: '1px solid #333',
      borderRadius: '8px',
      padding: '1rem',
      marginBottom: '1rem',
      boxShadow: '0 0 5px #00ffe1',
    },
    fadedText: {
      color: '#888',
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>📅 Calendar Manager</h2>

      <div style={{ marginBottom: '2rem' }}>
        <input
          type="text"
          placeholder="Event Title"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          style={styles.input}
        />
        <input
          type="datetime-local"
          value={start}
          onChange={(e) => setStart(e.target.value)}
          style={styles.input}
        />
        <input
          type="datetime-local"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
          style={styles.input}
        />
        <button onClick={createEvent} style={styles.button}>
          Create Event
        </button>
      </div>

      <h3 style={{ ...styles.heading, fontSize: '1.5rem' }}>Upcoming Events</h3>
      {events.length === 0 ? (
        <p style={styles.fadedText}>No events yet.</p>
      ) : (
        events.map((event) => (
          <div key={event.id} style={styles.eventCard}>
            <strong>{event.summary}</strong>
            <br />
            {event.start?.dateTime || event.start?.date} → {event.end?.dateTime || event.end?.date}
          </div>
        ))
      )}
    </div>
  );
};

export default CalendarManager;
