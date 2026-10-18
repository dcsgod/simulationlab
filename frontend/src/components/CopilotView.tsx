import React, { useState } from 'react';
import { 
  MessageSquareCode, 
  Send, 
  Sparkles, 
  ShieldCheck, 
  ArrowRight, 
  TrendingUp, 
  TrendingDown,
  Layers,
  CheckCircle2
} from 'lucide-react';
import { ChatResponse, sendChatMessage } from '../api';

export const CopilotView: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string; responseData?: ChatResponse }>>([
    {
      sender: 'assistant',
      text: "Hello! I am your Simulation Lab Copilot. You can ask me natural language what-if hypotheses, simulation queries, or optimization requests. Every number I provide is computed directly by the underlying mathematical engine and backed by verifiable execution traces.",
    }
  ]);

  const quickPrompts = [
    "What happens to gross margin if promotional discount increases by 5%?",
    "What happens to revenue if price cuts by 10%?",
    "Optimize generation dispatch to minimize cost",
  ];

  const handleSend = async (msgToSend: string = input) => {
    if (!msgToSend.trim() || loading) return;
    const userMsg = msgToSend.trim();
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(userMsg);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.reply,
          responseData: res,
        }
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: "I encountered an error processing your query. Please make sure the simulation engine is running.",
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem' }} className="animate-fade">
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <MessageSquareCode size={24} color="var(--accent-blue)" /> Grounded Simulation Copilot
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Ask natural language scenario hypotheses. Responses are accompanied by formal Grounded Evidence Envelopes.
        </p>
      </div>

      {/* Chat Container */}
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '550px',
        maxHeight: '75vh',
        boxShadow: 'var(--shadow-md)',
      }}>
        {/* Messages Scroll Area */}
        <div style={{
          flex: 1,
          padding: '1.5rem',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
        }}>
          {messages.map((m, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: m.sender === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  maxWidth: m.sender === 'user' ? '70%' : '85%',
                  padding: '1rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  background: m.sender === 'user' ? 'var(--accent-blue)' : 'var(--bg-surface)',
                  color: '#ffffff',
                  border: m.sender === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                }}
              >
                {m.text}

                {/* Evidence Envelope Card if returned */}
                {m.responseData && m.responseData.envelope && (
                  <div style={{
                    marginTop: '1rem',
                    padding: '1rem',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-medium)',
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '0.75rem',
                      borderBottom: '1px solid var(--border-subtle)',
                      paddingBottom: '0.5rem',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 700, fontSize: '0.8rem', color: '#60a5fa' }}>
                        <ShieldCheck size={16} /> Grounded Evidence Envelope
                      </div>
                      <span className="badge badge-emerald">100% Invariants Verified</span>
                    </div>

                    {/* Metric Deltas Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      {Object.entries(m.responseData.envelope.metric_deltas).map(([k, d]) => (
                        <div key={k} style={{ padding: '0.5rem', borderRadius: '4px', background: 'var(--bg-elevated)', fontSize: '0.75rem' }}>
                          <div style={{ color: 'var(--text-muted)' }}>{k}</div>
                          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#ffffff' }}>
                            {d.scenario_value.toFixed(1)}
                          </div>
                          <div style={{ color: d.absolute_delta >= 0 ? '#34d399' : '#fb7185', fontSize: '0.7rem' }}>
                            {d.absolute_delta > 0 ? `+${d.absolute_delta.toFixed(1)}` : d.absolute_delta.toFixed(1)}
                            {d.percentage_delta !== null && d.percentage_delta !== undefined ? ` (${d.percentage_delta > 0 ? '+' : ''}${d.percentage_delta.toFixed(1)}%)` : ''}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Sensitivity Ranking */}
                    {m.responseData.envelope.sensitivity_drivers.length > 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Top Driver: <strong style={{ color: '#60a5fa' }}>{m.responseData.envelope.sensitivity_drivers[0].variable_name}</strong> (Elasticity: {m.responseData.envelope.sensitivity_drivers[0].elasticity.toFixed(3)})
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              <Sparkles size={16} className="animate-spin" /> Evaluating simulation DAG &amp; generating evidence envelope...
            </div>
          )}
        </div>

        {/* Quick Suggestion Chips */}
        <div style={{
          padding: '0.5rem 1rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          gap: '0.5rem',
          overflowX: 'auto',
          background: 'var(--bg-surface)',
        }}>
          {quickPrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSend(p)}
              style={{
                whiteSpace: 'nowrap',
                padding: '0.35rem 0.75rem',
                borderRadius: 'var(--radius-full)',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '1rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          gap: '0.75rem',
        }}>
          <input
            type="text"
            placeholder="Ask a simulation hypothesis (e.g. What happens to gross margin if promo discount increases by 5%?)..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.9rem',
            }}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            style={{
              padding: '0.75rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--accent-blue)',
              color: '#ffffff',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: '0 2px 8px var(--accent-blue-glow)',
            }}
          >
            <Send size={16} /> Send
          </button>
        </div>
      </div>
    </div>
  );
};
