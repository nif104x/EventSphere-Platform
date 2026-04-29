import { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getChatRooms, getChatMessages, sendChatMessage, openChatRoomForEvent } from '../api';
import { sortChatRoomsLatest } from '../customerSort';
import '../customer-chat.css';

const pollMs = 4000;

export default function CustomerChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [rooms, setRooms] = useState([]);
  const [activeRoomId, setActiveRoomId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const [bootError, setBootError] = useState('');

  const refreshRooms = useCallback(async () => {
    const { data } = await getChatRooms();
    setRooms(sortChatRoomsLatest(Array.isArray(data) ? data : []));
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setBootError('');
      setError('');
      try {
        const eventId = searchParams.get('eventId');
        if (eventId) {
          const { data } = await openChatRoomForEvent(eventId);
          if (cancelled) return;
          setActiveRoomId(data.room_id);
          setSearchParams({}, { replace: true });
        }
        await refreshRooms();
      } catch (e) {
        if (!cancelled) {
          const d = e.response?.data?.detail;
          setBootError(typeof d === 'string' ? d : 'Could not open chat for that event.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [searchParams, setSearchParams, refreshRooms]);

  useEffect(() => {
    if (!activeRoomId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    let intervalId;
    const pull = async () => {
      try {
        const { data } = await getChatMessages(activeRoomId);
        if (!cancelled) setMessages(data.messages || []);
        setError('');
      } catch (e) {
        if (!cancelled) {
          const d = e.response?.data?.detail;
          setError(typeof d === 'string' ? d : 'Failed to load messages.');
        }
      }
    };
    pull();
    intervalId = setInterval(pull, pollMs);
    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [activeRoomId]);

  const activeRoom = rooms.find((r) => r.room_id === activeRoomId);

  const onSend = async (e) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !activeRoomId || sending) return;
    setSending(true);
    try {
      await sendChatMessage(activeRoomId, text);
      setDraft('');
      const { data } = await getChatMessages(activeRoomId);
      setMessages(data.messages || []);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(typeof d === 'string' ? d : 'Send failed.');
    }
    setSending(false);
  };

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--chat org-muted">Loading messages…</div>
    );
  }

  return (
    <div className="page-wrap org-page es-page es-page--chat">
      <header className="page-header">
        <h1 className="es-page-title">Messages</h1>
        <p className="muted es-chat__hint">
          Message vendors you have booked with. Each booking has its own conversation thread.
        </p>
      </header>

      {bootError ? <p className="error-banner">{bootError}</p> : null}
      {error ? <p className="error-banner">{error}</p> : null}

      <div className="es-chat">
        <div className="es-chat__layout">
          <aside className="es-chat__sidebar" aria-label="Conversations">
            <div className="es-chat__sidebar-head">Conversations</div>
            {rooms.length === 0 ? (
              <div className="es-chat__empty">
                <p>No conversations yet.</p>
                <p className="es-chat__hint">
                  After you book, start a thread from <Link to="/dashboard">your dashboard</Link>. Each event keeps
                  one conversation with that vendor.
                </p>
              </div>
            ) : (
              <ul className="es-chat__room-list">
                {rooms.map((r) => (
                  <li key={r.room_id}>
                    <button
                      type="button"
                      className={`es-chat__room${r.room_id === activeRoomId ? ' es-chat__room--active' : ''}`}
                      onClick={() => setActiveRoomId(r.room_id)}
                    >
                      <span className="es-chat__room-title">{r.company_name}</span>
                      <span className="es-chat__room-meta">
                        Event {r.event_id} · {r.room_id}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>

          <section className="es-chat__main" aria-label="Messages">
            {!activeRoomId ? (
              <div className="es-chat__empty">
                <p>Select a conversation or start one from your dashboard.</p>
              </div>
            ) : (
              <>
                <div className="es-chat__main-head">
                  <h2>{activeRoom?.company_name ?? 'Vendor'}</h2>
                  <p>
                    Event <strong>{activeRoom?.event_id}</strong> · Room <code>{activeRoomId}</code>
                  </p>
                </div>
                <div className="es-chat__stream" role="log" aria-live="polite">
                  {messages.length === 0 ? (
                    <p className="es-chat__empty" style={{ margin: 'auto' }}>
                      No messages yet. Say hello to your vendor.
                    </p>
                  ) : (
                    messages.map((m) => (
                      <div
                        key={m.id}
                        className={`es-chat__bubble ${m.is_mine ? 'es-chat__bubble--mine' : 'es-chat__bubble--them'}`}
                      >
                        {m.text}
                        {m.time ? <time>{m.time}</time> : null}
                      </div>
                    ))
                  )}
                </div>
                <form className="es-chat__composer" onSubmit={onSend}>
                  <input
                    type="text"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Type a message…"
                    autoComplete="off"
                    maxLength={8000}
                    aria-label="Message text"
                  />
                  <button type="submit" className="btn primary" disabled={sending || !draft.trim()}>
                    {sending ? 'Sending…' : 'Send'}
                  </button>
                </form>
              </>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
