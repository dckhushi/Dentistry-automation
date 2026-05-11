 🦷 Dentistry Automation

AI-powered multi-agent Voice Automation platform for dental clinics that handles inbound patient calls, insurance verification, claim follow-ups, appointment recalls, and payment collection through real-time conversational AI and adaptive IVR navigation.

Built using FastAPI, Twilio, Deepgram, Cartesia, Redis, PostgreSQL, and Next.js with a scalable, HIPAA-aware architecture designed for real-world healthcare automation.

---

# 🚀 Features

## 📞 AI Receptionist (Inbound)

* Answers patient calls 24/7
* Appointment booking and rescheduling
* Patient intake automation
* FAQ handling
* SMS confirmations
* Smart escalation to human staff

## 🏥 Insurance Verification Agent

* Outbound payer calls
* Automated IVR navigation
* Eligibility verification
* Deductible, copay, and benefits extraction
* Structured PMS-ready outputs

## 📋 Claim Follow-Up Agent

* Checks claim status automatically
* Retrieves denial codes and next actions
* Creates structured AR notes
* Reduces manual insurance follow-up workload

## 🔁 Recall Agent

* Calls overdue patients
* Reminder and rescheduling automation
* Multi-attempt retry logic
* DNC handling

## 💳 Revenue Collection Agent

* Handles balance follow-ups
* Sends payment links through SMS
* Logs payment promises and disputes
* Collections escalation workflow

## 🧠 Adaptive IVR Learning Engine

One of the core differentiators of the platform.

The system dynamically learns payer IVR phone trees instead of relying on hardcoded flows.

Features include:

* IVR graph-based learning
* DTMF replay optimization
* Confidence scoring
* Reinforcement learning loop
* Payer-specific timing calibration
* Automatic path optimization over time

This significantly reduces:

* Call duration
* LLM usage
* Operational cost
* Manual intervention

---

# 🏗️ System Architecture

## Core Layers

### 1. Telephony Layer

* Twilio Media Streams
* SMS support
* DTMF handling
* SIP trunk integration

### 2. Real-Time Voice Pipeline

* Deepgram Streaming STT
* Claude Haiku / Sonnet
* Cartesia TTS
* Low-latency conversational streaming

### 3. AI Orchestration Layer

* Async call controller
* Context management
* Session routing
* Prompt injection system

### 4. Agent Framework

* Shared tool layer
* Modular agent architecture
* Structured output schemas
* Escalation handling

### 5. IVR Navigation Engine

* Menu classification
* Path memory
* Reinforcement scoring
* Adaptive navigation

### 6. Storage Layer

* PostgreSQL
* Redis
* AWS S3
* HIPAA-aware storage design

### 7. Admin Dashboard

* Live call monitoring
* Transcript viewer
* IVR path manager
* Usage analytics

---

# ⚙️ Tech Stack

| Layer           | Technology            |
| --------------- | --------------------- |
| Backend         | FastAPI (Python)      |
| Frontend        | Next.js + React       |
| Real-Time Audio | Twilio Media Streams  |
| STT             | Deepgram Nova-2       |
| LLM             | Claude Haiku / Sonnet |
| TTS             | Cartesia / ElevenLabs |
| Database        | PostgreSQL            |
| Cache           | Redis                 |
| Storage         | AWS S3                |
| Task Queue      | Celery                |
| Deployment      | Fly.io / Railway      |
| Authentication  | Supabase Auth         |
| CI/CD           | GitHub Actions        |

---

# 📂 Project Structure

```bash
Dentistry-automation/
│
├── backend/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── ivr/
│   └── main.py
│
├── frontend/
│   ├── app/
│   ├── public/
│   └── package.json
│
├── requirements.txt
└── README.md
```

---

# 🔄 Real-Time Voice Flow

```text
Caller Audio
   ↓
Deepgram STT
   ↓
AI Agent Orchestration
   ↓
Claude LLM
   ↓
Cartesia TTS
   ↓
Audio Response to Caller
```

Target latency: **<500ms end-to-end**

---

# 🧠 IVR Learning Workflow

```text
Payer Call
   ↓
IVR Detection
   ↓
Path Lookup (Redis/Postgres)
   ↓
Known Path? → Replay DTMF
   ↓
Unknown Path? → Explore + Learn
   ↓
Confidence Scoring
   ↓
Path Optimization
```

---

# 🔐 Security & HIPAA Considerations

* AES-256 encrypted storage
* TLS-secured database connections
* Redis TTL session cleanup
* Row Level Security (RLS)
* Environment-based secret management
* Twilio webhook verification
* MFA-ready admin authentication
* PHI-safe logging architecture

---

# 📊 Cost Optimization Strategy

The platform is heavily optimized for real-world healthcare operational costs.

Key optimizations include:

* IVR path caching
* LLM gating
* Hold-state STT reduction
* Pre-rendered TTS phrases
* Lightweight inference models
* Batch extraction APIs
* SIP routing optimization

---

# 🚧 Current Status

## MVP In Progress

### Completed

* Project architecture
* Agent framework
* Backend scaffold
* Frontend scaffold
* IVR module structure
* GitHub integration

### Planned

* Real-time voice pipeline
* Insurance IVR learning
* Dashboard integration
* PMS connectors
* Multi-clinic onboarding
* Production deployment

---

# 🛠️ Installation

## Clone Repository

```bash
git clone https://github.com/dckhushi/Dentistry-automation.git
cd Dentistry-automation
```

## Backend Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

# 🌍 Future Scope

* Autonomous insurance appeal filing
* Voice biometrics
* Multi-language patient support
* AI-powered analytics
* Predictive scheduling
* Revenue forecasting
* Smart call prioritization
* Multi-speciality healthcare support

---

# 👩‍💻 Author

**Khushi**

MSc Integrated Data Science Student
AI • Voice Automation • Agentic Systems • Healthcare AI

---

# ⭐ Vision

To build scalable AI systems that reduce operational burden in healthcare while improving patient experience, efficiency, and accessibility through intelligent voice automation.
