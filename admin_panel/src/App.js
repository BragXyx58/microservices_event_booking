import React, { useState, useEffect } from 'react';

const USER_SERVICE_URL = "http://localhost:8001";
const EVENT_SERVICE_URL = "http://localhost:8002";
const BOOKING_SERVICE_URL = "http://localhost:8003";

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || '');
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  
  const [activeTab, setActiveTab] = useState('events');
  const [events, setEvents] = useState([]);
  const [users, setUsers] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [logs, setLogs] = useState([]);
  const [newEvent, setNewEvent] = useState({ title: '', description: '', total_seats: '' });

  const handleAuth = async (e) => {
    e.preventDefault();
    const endpoint = isRegisterMode ? '/register' : '/login';
    
    try {
      const response = await fetch(`${USER_SERVICE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await response.json();
      
      if (response.ok) {
        if (isRegisterMode) {
          setSuccessMsg('Registration successful! Please login.');
          setIsRegisterMode(false);
          setError('');
        } else {
          setToken(data.token);
          setRole(data.role);
          localStorage.setItem('token', data.token);
          localStorage.setItem('role', data.role);
          setError('');
        }
      } else {
        setError(data.error || 'Authentication failed');
      }
    } catch (err) {
      setError('Failed to connect to auth service.');
    }
  };

  const handleLogout = () => {
    setToken(''); setRole('');
    localStorage.removeItem('token'); localStorage.removeItem('role');
    setEvents([]); setUsers([]); setBookings([]); setLogs([]);
  };

  const fetchWithAuth = async (url) => {
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error('Failed to fetch data');
    return response.json();
  };

  const loadData = async () => {
    try {
      if (activeTab === 'events' || role === 'user') {
        const data = await fetchWithAuth(`${EVENT_SERVICE_URL}/events`);
        setEvents(data);
      } else if (activeTab === 'users' && role === 'admin') {
        const data = await fetchWithAuth(`${USER_SERVICE_URL}/admin/users`);
        setUsers(data);
      } else if (activeTab === 'bookings' && role === 'admin') {
        const data = await fetchWithAuth(`${BOOKING_SERVICE_URL}/admin/bookings`);
        setBookings(data);
      } else if (activeTab === 'logs' && role === 'admin') {
        const data = await fetchWithAuth(`${BOOKING_SERVICE_URL}/admin/logs`);
        setLogs(data);
      }
      setError('');
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (token) loadData();
  }, [token, activeTab, role]);

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${EVENT_SERVICE_URL}/admin/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          title: newEvent.title,
          description: newEvent.description,
          total_seats: parseInt(newEvent.total_seats)
        })
      });
      if (response.ok) {
        setNewEvent({ title: '', description: '', total_seats: '' });
        loadData();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to create event');
      }
    } catch (err) { setError('Error connecting to server'); }
  };

  const handleBookEvent = async (eventId) => {
    try {
      const response = await fetch(`${BOOKING_SERVICE_URL}/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ event_id: eventId })
      });
      
      const data = await response.json();
      if (response.ok) {
        alert("Successfully booked!");
        loadData();
      } else {
        alert(data.error || "Booking failed");
      }
    } catch (err) { alert("Error connecting to booking service"); }
  };

  if (!token) {
    return (
      <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '400px', margin: '0 auto' }}>
        <h2>{isRegisterMode ? 'User Registration' : 'Login'}</h2>
        {successMsg && <p style={{color: 'green'}}>{successMsg}</p>}
        {error && <p style={{color: 'red'}}>{error}</p>}
        <form onSubmit={handleAuth}>
          <div style={{ marginBottom: '10px' }}><label>Username: </label><input value={username} onChange={e => setUsername(e.target.value)} required /></div>
          <div style={{ marginBottom: '10px' }}><label>Password: </label><input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></div>
          <button type="submit" style={{ marginRight: '10px' }}>{isRegisterMode ? 'Register' : 'Login'}</button>
          <button type="button" onClick={() => {setIsRegisterMode(!isRegisterMode); setError(''); setSuccessMsg('');}}>
            {isRegisterMode ? 'Switch to Login' : 'Switch to Registration'}
          </button>
        </form>
      </div>
    );
  }

  if (role === 'admin') {
    return (
      <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
        <h2>Admin Dashboard</h2>
        <button onClick={handleLogout} style={{ marginBottom: '20px' }}>Logout</button>
        {error && <p style={{color: 'red'}}>{error}</p>}
        <div style={{ marginBottom: '20px' }}>
          <button onClick={() => setActiveTab('events')} style={{ fontWeight: activeTab === 'events' ? 'bold' : 'normal' }}>Events</button>
          <button onClick={() => setActiveTab('users')} style={{ marginLeft: '10px', fontWeight: activeTab === 'users' ? 'bold' : 'normal' }}>Users</button>
          <button onClick={() => setActiveTab('bookings')} style={{ marginLeft: '10px', fontWeight: activeTab === 'bookings' ? 'bold' : 'normal' }}>Bookings</button>
          <button onClick={() => setActiveTab('logs')} style={{ marginLeft: '10px', fontWeight: activeTab === 'logs' ? 'bold' : 'normal' }}>System Logs</button>
        </div>

        {activeTab === 'events' && (
          <div>
            <h3>Create New Event</h3>
            <form onSubmit={handleCreateEvent} style={{ marginBottom: '20px', padding: '10px', border: '1px solid #ccc' }}>
              <input placeholder="Title" value={newEvent.title} onChange={e => setNewEvent({...newEvent, title: e.target.value})} required style={{ marginRight: '10px' }}/>
              <input placeholder="Description" value={newEvent.description} onChange={e => setNewEvent({...newEvent, description: e.target.value})} style={{ marginRight: '10px' }}/>
              <input placeholder="Total Seats" type="number" min="1" value={newEvent.total_seats} onChange={e => setNewEvent({...newEvent, total_seats: e.target.value})} required style={{ marginRight: '10px' }}/>
              <button type="submit">Create</button>
            </form>
            <Table data={events} type="events" />
          </div>
        )}
        {activeTab === 'users' && <div><h3>Users List</h3><Table data={users} type="users" /></div>}
        {activeTab === 'bookings' && <div><h3>Bookings List</h3><Table data={bookings} type="bookings" /></div>}
        {activeTab === 'logs' && (
          <div>
            <h3>System Logs (RabbitMQ)</h3>
            <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead><tr style={{ backgroundColor: '#f2f2f2' }}><th>Timestamp</th><th>Event Data</th></tr></thead>
              <tbody>
                {logs.map((log, i) => (
                  <tr key={i}>
                    <td>{log.timestamp}</td>
                    <td><pre>{JSON.stringify(log.event, null, 2)}</pre></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>User Dashboard - Book Your Events!</h2>
      <button onClick={handleLogout} style={{ marginBottom: '20px' }}>Logout</button>
      {error && <p style={{color: 'red'}}>{error}</p>}
      
      <h3>Available Events</h3>
      <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead><tr><th>Title</th><th>Description</th><th>Available Seats</th><th>Action</th></tr></thead>
        <tbody>
          {events.map(ev => (
            <tr key={ev.id}>
              <td>{ev.title}</td>
              <td>{ev.description}</td>
              <td>{ev.available_seats} / {ev.total_seats}</td>
              <td>
                <button onClick={() => handleBookEvent(ev.id)} disabled={ev.available_seats <= 0}>
                  {ev.available_seats > 0 ? 'Book Ticket' : 'Sold Out'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Table({ data, type }) {
  if (!data || data.length === 0) return <p>No data available.</p>;
  const keys = Object.keys(data[0]);
  return (
    <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
      <thead><tr style={{ backgroundColor: '#f2f2f2' }}>{keys.map(k => <th key={k}>{k.toUpperCase()}</th>)}</tr></thead>
      <tbody>{data.map((row, i) => <tr key={i}>{keys.map(k => <td key={k}>{row[k]}</td>)}</tr>)}</tbody>
    </table>
  );
}

export default App;