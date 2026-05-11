'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Phone, AlertTriangle, Activity, Brain, Shield, TrendingUp, CheckCircle, RefreshCw, ChevronRight, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

const API = 'http://127.0.0.1:8000';

interface Call { id: string; twilio_call_sid: string; agent_type: string; caller_number: string; status: string; duration_s: number; cost_usd: number; is_emergency: boolean; created_at: string; }
interface IVRPath { id: string; payer_id: string; task_type: string; confidence: number; success_count: number; avg_duration_s: number; }
interface Stats { total_calls: number; emergency_calls: number; ivr_paths_learned: number; high_confidence_paths: number; cost_per_minute: { active_conversation: string; on_hold: string; golden_ivr_path: string; }; }
interface Message { role: 'patient' | 'aria'; text: string; action?: string; emergency?: boolean; timestamp: Date; }

function Badge({ type }: { type: string }) {
  const styles: Record<string, string> = { receptionist: 'background:#e8f3f0;color:#1a6b5a', insurance: 'background:#eff4fb;color:#2563a8', claim_followup: 'background:#fef6ec;color:#d4821a', recall: 'background:#f3f0fb;color:#6b3fa0', revenue: 'background:#fdf0ef;color:#c0392b' };
  const labels: Record<string, string> = { receptionist: 'Receptionist', insurance: 'Insurance', claim_followup: 'Claim Follow-Up', recall: 'Recall', revenue: 'Revenue' };
  return <span style={{ ...Object.fromEntries((styles[type] || 'background:#f2f1ee;color:#6b6860').split(';').map(s => s.split(':'))), padding: '2px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 500 }}>{labels[type] || type}</span>;
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 90 ? '#1a6b5a' : pct >= 70 ? '#2563a8' : pct >= 40 ? '#d4821a' : '#c0392b';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, height: 4, background: '#f2f1ee', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.6s ease' }} />
      </div>
      <span style={{ fontFamily: 'DM Mono, monospace', fontSize: 12, color, fontWeight: 500, minWidth: 32 }}>{pct}%</span>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, color }: { icon: any, label: string, value: string | number, sub?: string, color: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500, letterSpacing: '0.04em', textTransform: 'uppercase' }}>{label}</span>
        <div style={{ background: color + '18', borderRadius: 8, padding: 8 }}><Icon size={16} color={color} /></div>
      </div>
      <div>
        <div style={{ fontSize: 28, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1 }}>{value}</div>
        {sub && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [paths, setPaths] = useState<IVRPath[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [activeTab, setActiveTab] = useState<'calls' | 'ivr' | 'demo'>('demo');
  const [messages, setMessages] = useState<Message[]>([]);
  const [demoMsg, setDemoMsg] = useState('');
  const [demoLoading, setDemoLoading] = useState(false);
  const [callSid] = useState('DEMO_' + Math.random().toString(36).slice(2, 8));
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [transcript, setTranscript] = useState('');
  const [voiceStatus, setVoiceStatus] = useState('Click mic to speak');
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchData(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    synthRef.current = window.speechSynthesis;
    return () => { synthRef.current?.cancel(); };
  }, []);

  const fetchData = async () => {
    try {
      const [callsRes, pathsRes, statsRes] = await Promise.all([
        fetch(`${API}/api/calls`), fetch(`${API}/api/ivr/paths`), fetch(`${API}/api/stats`)
      ]);
      setCalls((await callsRes.json()).calls || []);
      setPaths((await pathsRes.json()).paths || []);
      setStats(await statsRes.json());
    } catch (e) { console.error(e); }
  };

  const speak = useCallback((text: string) => {
    if (!voiceEnabled || !synthRef.current) return;
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synthRef.current.getVoices();
    const preferred = voices.find(v => v.name.includes('Samantha') || v.name.includes('Karen') || v.name.includes('Victoria') || v.name.includes('Female') || (v.lang === 'en-US' && v.name.includes('Google')));
    if (preferred) utterance.voice = preferred;
    utterance.rate = 1.05;
    utterance.pitch = 1.05;
    utterance.volume = 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => { setIsSpeaking(false); setVoiceStatus('Click mic to speak'); };
    setIsSpeaking(true);
    setVoiceStatus('Aria is speaking...');
    synthRef.current.speak(utterance);
  }, [voiceEnabled]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setDemoLoading(true);
    setDemoMsg('');
    const patientMsg: Message = { role: 'patient', text, timestamp: new Date() };
    setMessages(prev => [...prev, patientMsg]);

    try {
      const res = await fetch(`${API}/demo/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ call_sid: callSid, message: text, caller_number: '+1234567890' })
      });
      const data = await res.json();
      const ariaMsg: Message = { role: 'aria', text: data.ai_response, action: data.action, emergency: data.emergency, timestamp: new Date() };
      setMessages(prev => [...prev, ariaMsg]);
      if (voiceEnabled) speak(data.ai_response);
    } catch (e) { console.error(e); }
    finally { setDemoLoading(false); }
  }, [callSid, voiceEnabled, speak]);

  const startListening = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) { alert('Please use Chrome for voice features'); return; }

    if (isSpeaking) { synthRef.current?.cancel(); setIsSpeaking(false); }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => { setIsListening(true); setVoiceStatus('Listening...'); setTranscript(''); };
    recognition.onresult = (e: any) => {
      const t = Array.from(e.results).map((r: any) => r[0].transcript).join('');
      setTranscript(t);
      setVoiceStatus(`Heard: "${t}"`);
    };
    recognition.onend = () => {
      setIsListening(false);
      setTranscript(prev => { if (prev.trim()) { sendMessage(prev); } return ''; });
      setVoiceStatus('Processing...');
    };
    recognition.onerror = (e: any) => { setIsListening(false); setVoiceStatus('Error: ' + e.error); };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isSpeaking, sendMessage]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const quickMessages = [
    'Hi, I need to book a teeth cleaning appointment',
    'I have severe tooth pain, I cannot sleep, please help',
    'What insurance plans do you accept?',
    'I need to reschedule my appointment for next week',
    'What are your clinic hours and location?',
  ];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{ background: '#fff', borderBottom: '1px solid var(--border)', padding: '0 40px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 32, height: 32, background: 'var(--accent)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Phone size={16} color="#fff" /></div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>Dentistry Automation</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>VOICE AI PLATFORM</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {isSpeaking && <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent)', fontSize: 12 }}><Volume2 size={14} /><span>Aria speaking...</span></div>}
          {isListening && <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#c0392b', fontSize: 12 }}><Mic size={14} /><span>Listening...</span></div>}
          <span className="dot-live" />
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>System Online</span>
          <button onClick={fetchData} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-secondary)', fontSize: 12 }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </header>

      <main style={{ padding: '32px 40px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontFamily: 'Playfair Display, serif', fontSize: 28, fontWeight: 400 }}>Admin Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>Real-time overview of all voice AI agents and IVR learning activity</p>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
          <StatCard icon={Activity} label="Total Calls" value={stats?.total_calls ?? '—'} sub="All time" color="#1a6b5a" />
          <StatCard icon={AlertTriangle} label="Emergency Calls" value={stats?.emergency_calls ?? '—'} sub="Triaged immediately" color="#c0392b" />
          <StatCard icon={Brain} label="IVR Paths Learned" value={stats?.ivr_paths_learned ?? '—'} sub="Across all payers" color="#2563a8" />
          <StatCard icon={Shield} label="High Confidence" value={stats?.high_confidence_paths ?? '—'} sub="Paths > 70%" color="#d4821a" />
        </div>

        {/* Cost Banner */}
        <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '16px 24px', marginBottom: 32, display: 'flex', alignItems: 'center', gap: 40 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={16} color="var(--accent)" />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>Cost Per Minute</span>
          </div>
          {[{ label: 'Active Conversation', value: '$0.022–0.026', color: 'var(--accent)' }, { label: 'On Hold', value: '~$0.001', color: 'var(--blue)' }, { label: 'Golden IVR Path', value: '~$0.010', color: 'var(--warning)' }].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 1, height: 32, background: 'var(--border)' }} />
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{item.label}</div>
                <div style={{ fontFamily: 'DM Mono, monospace', fontSize: 15, fontWeight: 500, color: item.color }}>{item.value}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'var(--bg-subtle)', borderRadius: 10, padding: 4, width: 'fit-content' }}>
          {(['demo', 'calls', 'ivr'] as const).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{ padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 500, background: activeTab === tab ? '#fff' : 'transparent', color: activeTab === tab ? 'var(--text-primary)' : 'var(--text-secondary)', boxShadow: activeTab === tab ? '0 1px 4px rgba(0,0,0,0.08)' : 'none', transition: 'all 0.2s ease' }}>
              {tab === 'demo' ? '🎯 Live Voice Demo' : tab === 'ivr' ? 'IVR Learning' : 'Call Log'}
            </button>
          ))}
        </div>

        {/* LIVE VOICE DEMO TAB */}
        {activeTab === 'demo' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20 }}>

            {/* Chat window */}
            <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, display: 'flex', flexDirection: 'column', height: 600 }}>
              {/* Chat header */}
              <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span className="dot-live" />
                  <span style={{ fontWeight: 600, fontSize: 14 }}>Aria — AI Receptionist</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-subtle)', padding: '2px 8px', borderRadius: 10 }}>Smile Dental</span>
                </div>
                <button onClick={() => { setVoiceEnabled(v => !v); synthRef.current?.cancel(); }} style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: voiceEnabled ? 'var(--accent)' : 'var(--text-muted)' }}>
                  {voiceEnabled ? <><Volume2 size={12} /> Voice On</> : <><VolumeX size={12} /> Voice Off</>}
                </button>
              </div>

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
                {messages.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🦷</div>
                    <div style={{ fontWeight: 500, marginBottom: 6 }}>Hi, I'm Aria</div>
                    <div style={{ fontSize: 13 }}>Your AI dental receptionist. Click the mic or type to start.</div>
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'patient' ? 'flex-end' : 'flex-start', gap: 4 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>{msg.role === 'patient' ? 'You' : 'Aria'} · {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    {msg.emergency && (
                      <div style={{ background: 'var(--emergency-light)', border: '1px solid #f5c6c2', borderRadius: 8, padding: '8px 12px', display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                        <AlertTriangle size={14} color="var(--emergency)" />
                        <span style={{ fontSize: 12, color: 'var(--emergency)', fontWeight: 600 }}>Emergency Triage Activated — SMS sent to patient & dentist</span>
                      </div>
                    )}
                    <div style={{ maxWidth: '80%', padding: '12px 16px', borderRadius: msg.role === 'patient' ? '16px 16px 4px 16px' : '16px 16px 16px 4px', background: msg.role === 'patient' ? 'var(--accent)' : 'var(--bg-subtle)', color: msg.role === 'patient' ? '#fff' : 'var(--text-primary)', fontSize: 14, lineHeight: 1.6 }}>
                      {msg.text}
                    </div>
                    {msg.action && msg.action !== 'continue' && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'DM Mono, monospace' }}>action: {msg.action}</div>
                    )}
                  </div>
                ))}
                {demoLoading && (
                  <div style={{ display: 'flex', gap: 4, padding: '12px 16px', background: 'var(--bg-subtle)', borderRadius: '16px 16px 16px 4px', width: 'fit-content' }}>
                    {[0, 1, 2].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-muted)', animation: `pulse ${0.6 + i * 0.15}s ease-in-out infinite` }} />)}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Voice input bar */}
              <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)' }}>
                {isListening && transcript && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8, fontStyle: 'italic' }}>"{transcript}"</div>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  {/* Mic button */}
                  <button
                    onClick={isListening ? stopListening : startListening}
                    style={{ width: 44, height: 44, borderRadius: '50%', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', background: isListening ? '#c0392b' : 'var(--accent)', transition: 'all 0.2s', flexShrink: 0, boxShadow: isListening ? '0 0 0 4px rgba(192,57,43,0.2)' : 'none' }}
                  >
                    {isListening ? <MicOff size={18} color="#fff" /> : <Mic size={18} color="#fff" />}
                  </button>
                  <input
                    value={demoMsg}
                    onChange={e => setDemoMsg(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendMessage(demoMsg)}
                    placeholder={isListening ? 'Listening...' : 'Or type a message...'}
                    disabled={isListening}
                    style={{ flex: 1, border: '1px solid var(--border)', borderRadius: 22, padding: '10px 18px', fontSize: 13, outline: 'none', background: 'var(--bg)', color: 'var(--text-primary)', fontFamily: 'DM Sans, sans-serif' }}
                  />
                  <button onClick={() => sendMessage(demoMsg)} disabled={demoLoading || !demoMsg.trim()} style={{ background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: 22, padding: '10px 18px', cursor: 'pointer', fontSize: 13, fontWeight: 500, opacity: (!demoMsg.trim() || demoLoading) ? 0.5 : 1 }}>
                    Send
                  </button>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>{voiceStatus}</div>
              </div>
            </div>

            {/* Right panel */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Quick messages */}
              <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '20px' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: 12 }}>Try These</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {quickMessages.map(msg => (
                    <button key={msg} onClick={() => sendMessage(msg)} style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', textAlign: 'left', cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', transition: 'all 0.15s' }}>
                      <span>{msg}</span>
                      <ChevronRight size={12} style={{ flexShrink: 0 }} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Voice status card */}
              <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '20px' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: 12 }}>Voice Pipeline Status</div>
                {[
                  { label: 'STT', value: 'Web Speech API', status: 'active', sub: 'Chrome built-in, free' },
                  { label: 'LLM', value: 'Groq LLaMA 3.1', status: 'active', sub: 'Free tier, ~150ms' },
                  { label: 'TTS', value: 'Speech Synthesis', status: 'active', sub: 'Chrome built-in, free' },
                  { label: 'Latency', value: '< 500ms', status: 'active', sub: 'End-to-end target' },
                ].map(item => (
                  <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 500 }}>{item.label}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.sub}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 12, fontFamily: 'DM Mono, monospace', color: 'var(--accent)' }}>{item.value}</div>
                      <div style={{ fontSize: 10, color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end' }}><span className="dot-live" style={{ width: 6, height: 6 }} />{item.status}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Agent info */}
              <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, padding: '20px' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.04em', textTransform: 'uppercase', marginBottom: 12 }}>5 AI Agents</div>
                {[
                  { name: 'AI Receptionist', type: 'receptionist', desc: 'Inbound calls, booking' },
                  { name: 'Insurance Verifier', type: 'insurance', desc: 'Outbound payer calls' },
                  { name: 'Claim Follow-Up', type: 'claim_followup', desc: 'AR & denial handling' },
                  { name: 'Recall Agent', type: 'recall', desc: 'Patient reactivation' },
                  { name: 'Revenue Agent', type: 'revenue', desc: 'Balance collection' },
                ].map(agent => (
                  <div key={agent.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 500 }}>{agent.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{agent.desc}</div>
                    </div>
                    <Badge type={agent.type} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Call Log Tab */}
        {activeTab === 'calls' && (
          <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 600 }}>Recent Calls</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{calls.length} records</span>
            </div>
            {calls.length === 0 ? (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
                <Phone size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                <div>No calls yet. Use the Live Voice Demo tab to simulate a call.</div>
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead><tr style={{ background: 'var(--bg-subtle)' }}>
                  {['Agent', 'Caller', 'Status', 'Duration', 'Emergency', 'Time'].map(h => (
                    <th key={h} style={{ padding: '10px 20px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {calls.map(call => (
                    <tr key={call.id} style={{ borderTop: '1px solid var(--border)', background: call.is_emergency ? 'var(--emergency-light)' : 'transparent' }}>
                      <td style={{ padding: '14px 20px' }}><Badge type={call.agent_type} /></td>
                      <td style={{ padding: '14px 20px', fontFamily: 'DM Mono, monospace', fontSize: 12, color: 'var(--text-secondary)' }}>{call.caller_number}</td>
                      <td style={{ padding: '14px 20px' }}><span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><CheckCircle size={8} color="var(--text-muted)" /><span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{call.status}</span></span></td>
                      <td style={{ padding: '14px 20px', fontFamily: 'DM Mono, monospace', fontSize: 12 }}>{call.duration_s}s</td>
                      <td style={{ padding: '14px 20px' }}>{call.is_emergency ? <span style={{ color: 'var(--emergency)', fontSize: 12, fontWeight: 600 }}>⚠ Emergency</span> : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>}</td>
                      <td style={{ padding: '14px 20px', fontSize: 12, color: 'var(--text-muted)' }}>{new Date(call.created_at).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* IVR Tab */}
        {activeTab === 'ivr' && (
          <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
            <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontWeight: 600 }}>Learned IVR Paths</span>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>Confidence increases with every successful call. Golden paths (≥90%) use zero LLM cost.</p>
            </div>
            {paths.length === 0 ? (
              <div style={{ padding: 60, textAlign: 'center', color: 'var(--text-muted)' }}>
                <Brain size={32} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
                <div>No IVR paths learned yet.</div>
              </div>
            ) : (
              <div style={{ padding: 24, display: 'grid', gap: 12 }}>
                {paths.map(path => (
                  <div key={path.id} style={{ border: '1px solid var(--border)', borderRadius: 10, padding: '16px 20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{path.payer_id.replace('_', ' ')}</div>
                        <Badge type={path.task_type} />
                      </div>
                      <div style={{ display: 'flex', gap: 20 }}>
                        <div style={{ textAlign: 'right' }}><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Successes</div><div style={{ fontFamily: 'DM Mono, monospace', fontWeight: 500 }}>{path.success_count}</div></div>
                        <div style={{ textAlign: 'right' }}><div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Avg Duration</div><div style={{ fontFamily: 'DM Mono, monospace', fontWeight: 500 }}>{path.avg_duration_s}s</div></div>
                      </div>
                    </div>
                    <ConfidenceBar value={path.confidence} />
                    {path.confidence >= 0.9 && <div style={{ marginTop: 8, fontSize: 11, color: 'var(--accent)', fontWeight: 600 }}>✦ Golden Path — Zero LLM cost on replay</div>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}