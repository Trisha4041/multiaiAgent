import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog';
import { Calendar, Users, PlusCircle, Trash2, Edit2 } from 'lucide-react';

const GoogleCalendarManager = () => {
  const [events, setEvents] = useState([]);
  const [calendars, setCalendars] = useState([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState('padgelwartrisha91@gmail.com');
  const [newEvent, setNewEvent] = useState({
    summary: '',
    startTime: '',
    endTime: ''
  });
  const [editingEvent, setEditingEvent] = useState(null);

  // Fetch events
  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:5000/events');
      const data = await response.json();
      setEvents(data);
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  // Fetch calendars
  const fetchCalendars = async () => {
    try {
      const response = await fetch('http://localhost:5000/calendars');
      const data = await response.json();
      setCalendars(data);
    } catch (error) {
      console.error('Error fetching calendars:', error);
    }
  };

  // Create event
  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5000/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newEvent),
      });
      const data = await response.json();
      fetchEvents();
      // Reset form
      setNewEvent({ summary: '', startTime: '', endTime: '' });
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  // Update event
  const handleUpdateEvent = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://localhost:5000/events/${editingEvent.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editingEvent),
      });
      const data = await response.json();
      fetchEvents();
      // Reset editing state
      setEditingEvent(null);
    } catch (error) {
      console.error('Error updating event:', error);
    }
  };

  // Delete event
  const handleDeleteEvent = async (eventId) => {
    try {
      await fetch(`http://localhost:5000/events/${eventId}`, {
        method: 'DELETE',
      });
      fetchEvents();
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  // Change calendar ID
  const handleChangeCalendarId = async () => {
    try {
      await fetch('http://localhost:5000/calendar-id', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ calendarId: selectedCalendarId }),
      });
      fetchEvents();
    } catch (error) {
      console.error('Error changing calendar ID:', error);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchEvents();
    fetchCalendars();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-6 w-6" /> Google Calendar Manager
            </CardTitle>
          </div>
          
          {/* Calendar ID Selector */}
          <div className="flex items-center gap-2">
            <Input 
              placeholder="Enter Calendar ID"
              value={selectedCalendarId}
              onChange={(e) => setSelectedCalendarId(e.target.value)}
              className="w-64"
            />
            <Button variant="outline" onClick={handleChangeCalendarId}>
              Change
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {/* Event Creation Dialog */}
          <Dialog>
            <DialogTrigger asChild>
              <Button className="mb-4">
                <PlusCircle className="mr-2 h-4 w-4" /> Create Event
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Event</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateEvent} className="space-y-4">
                <div>
                  <Label>Event Title</Label>
                  <Input 
                    value={newEvent.summary}
                    onChange={(e) => setNewEvent({...newEvent, summary: e.target.value})}
                    required 
                  />
                </div>
                <div>
                  <Label>Start Time</Label>
                  <Input 
                    type="datetime-local"
                    value={newEvent.startTime}
                    onChange={(e) => setNewEvent({...newEvent, startTime: e.target.value})}
                    required 
                  />
                </div>
                <div>
                  <Label>End Time</Label>
                  <Input 
                    type="datetime-local"
                    value={newEvent.endTime}
                    onChange={(e) => setNewEvent({...newEvent, endTime: e.target.value})}
                    required 
                  />
                </div>
                <Button type="submit">Create Event</Button>
              </form>
            </DialogContent>
          </Dialog>

          {/* Available Calendars */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Users className="h-5 w-5" /> Available Calendars
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {calendars.map((cal) => (
                <div key={cal.id} className="p-2 border rounded">
                  <p className="font-medium">{cal.summary}</p>
                  <p className="text-sm text-gray-500">{cal.id}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Events List */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Upcoming Events</h3>
            {events.length === 0 ? (
              <p>No upcoming events</p>
            ) : (
              <div className="space-y-2">
                {events.map((event) => (
                  <div 
                    key={event.id} 
                    className="flex items-center justify-between p-3 border rounded"
                  >
                    <div>
                      <h4 className="font-medium">{event.summary}</h4>
                      <p className="text-sm text-gray-500">
                        {new Date(event.start.dateTime || event.start.date).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Edit Event Dialog */}
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button 
                            variant="outline" 
                            size="icon"
                            onClick={() => setEditingEvent(event)}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Edit Event</DialogTitle>
                          </DialogHeader>
                          <form onSubmit={handleUpdateEvent} className="space-y-4">
                            <div>
                              <Label>Event Title</Label>
                              <Input 
                                value={editingEvent?.summary || ''}
                                onChange={(e) => setEditingEvent({...editingEvent, summary: e.target.value})}
                                required 
                              />
                            </div>
                            <div>
                              <Label>Start Time</Label>
                              <Input 
                                type="datetime-local"
                                value={editingEvent?.start?.dateTime || ''}
                                onChange={(e) => setEditingEvent({
                                  ...editingEvent, 
                                  start: { ...editingEvent.start, dateTime: e.target.value }
                                })}
                                required 
                              />
                            </div>
                            <div>
                              <Label>End Time</Label>
                              <Input 
                                type="datetime-local"
                                value={editingEvent?.end?.dateTime || ''}
                                onChange={(e) => setEditingEvent({
                                  ...editingEvent, 
                                  end: { ...editingEvent.end, dateTime: e.target.value }
                                })}
                                required 
                              />
                            </div>
                            <Button type="submit">Update Event</Button>
                          </form>
                        </DialogContent>
                      </Dialog>

                      {/* Delete Event Button */}
                      <Button 
                        variant="destructive" 
                        size="icon"
                        onClick={() => handleDeleteEvent(event.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GoogleCalendarManager;