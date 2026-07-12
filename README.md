<!-- ========== ANIMATED HEADER BANNER ========== -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:22d3ee,100:8b5cf6&height=200&section=header&text=n8n%20AI%20Job%20Search%20CRM&fontSize=45&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Local%20Recruitment%20Automation%20%7C%20Gemini%20%7C%20Python%20%7C%20Docker&descAlignY=60&descAlign=50" width="100%">
</p>

<!-- ========== TYPING ANIMATION INTRO ========== -->
<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=24&duration=3000&pause=500&color=22D3EE&center=true&vCenter=true&width=600&lines=Local+n8n+Automation+Workflow;Google+Gemini+API+Integration;Python+Resume+%2F+Cover+Letter+Builders;SQLite+%26+openpyxl+Excel+CRM;Containerized+Docker+Environment" alt="Typing SVG">
</p>

<!-- ========== PROFILE VIEWS + FOLLOWERS BADGE ========== -->
<p align="center">
  <img src="https://komarev.com/ghpvc/?username=Sadique721&label=Repository%20Views&color=22d3ee&style=flat-square" alt="Repository views" />
  <img src="https://img.shields.io/github/stars/Sadique721/n8n-job-automation?label=Stars&style=social" alt="GitHub stars">
  <img src="https://img.shields.io/github/forks/Sadique721/n8n-job-automation?label=Forks&style=social" alt="GitHub forks">
</p>

---

## 🚀 Project Overview

The **Local AI Job Search & Application Tailoring CRM** is a containerized, 100% local recruitment automation system. It orchestrates job crawling, resume parsing, match scoring, database/spreadsheet logging, and tailored document generation using **n8n**, **Python**, and the **Google Gemini API**.

All assets, including SQLite records, custom-tailored `.docx`/`.pdf` resumes, and cover letters, are automatically compiled and stored locally in `D:\AI Job Automation\`.

---

## 🛠️ Used Technology Stack & Versions

| Category | Component / Tool | Version | Description |
|----------|------------------|---------|-------------|
| **Orchestration** | **n8n** | `^2.28.4` | Core event-driven workflow engine |
| **Runtime** | **Node.js** | `v20 (Bookworm slim)` | Base container runtime environment |
| **Runtime** | **Python** | `3.11+` | Backend script execution and doc compiler |
| **AI Model** | **Google Gemini API** | `v1` | Match scoring, resume parsing, and tailoring |
| **Local LLM** | **Ollama** | `v0.1.x` | Fallback local model execution (Qwen2.5) |
| **Database** | **SQLite** | `v3` | Log storage for candidate and job profiles |
| **Excel CRM** | **openpyxl** | `^3.1.5` | Excel worksheet and link formatting generator |
| **Word Docs** | **python-docx** | `^1.2.0` | Word processor for resume/cover letter tailoring |
| **PDF Docs** | **fpdf2** | `^2.8.7` | PDF builder with custom UTF-8 sanitizers |
| **DevOps** | **Docker & Compose** | `v2` | Multi-container environment orchestration |
| **Testing** | **unittest** | (Standard Library) | Isolated testing suite for backend helpers |

---

### 🧠 Core Project Badges

![n8n](https://img.shields.io/badge/n8n-FF6C37?style=for-the-badge&logo=n8n&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75C2?style=for-the-badge&logo=googlegemini&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## 📐 System Workflow Architecture

The automation pipeline executes event loops to find, score, and customize applications:

```mermaid
graph TD
    Trigger[Manual/Schedule Trigger] --> Init[Parse Resume.txt & config.json]
    Init --> NotifyStart[Telegram Alert: Search Started]
    NotifyStart --> ParseResume[Gemini: Parse Resume details]
    ParseResume --> NotifyResume[Telegram Alert: Resume Analyzed]
    NotifyResume --> Crawlers[Crawl Jobs]
    
    subgraph Crawlers [Live Internet Crawling]
        RemoteOK[RemoteOK API]
        Greenhouse[Greenhouse HTTP Scraper]
        Lever[Lever HTTP Scraper]
        Ashby[Ashby HTTP Scraper]
    end
    
    Crawlers --> Merge[Merge & Deduplicate Jobs]
    Merge --> NotifyFound[Telegram Alert: Discovered Jobs Count]
    NotifyFound --> Rank[Gemini: Score & Rank Jobs 0-100%]
    Rank --> Filter[Filter out low matches < 50%]
    Filter --> NotifyMatches[Telegram Alert: High Matches Found]
    NotifyMatches --> Loop[Loop Over High Match Jobs]
    
    Loop --> Tailor[Gemini: Tailor Resume Bullets & Cover Letter Opener]
    Tailor --> BuildPayload[Build CRM Payload]
    BuildPayload --> ExecutePython[Execute Local process_job.py]
    ExecutePython --> NotifyTailored[Telegram Alert: Assets Generated]
    NotifyTailored --> SendEmail[SMTP Email: Send Cold Email Draft to Self]
    SendEmail --> Loop
    
    Loop --> NotifyDone[Telegram Alert: Pipeline Completed]
    
    style Trigger fill:#4CAF50,stroke:#388E3C,color:#fff
    style Crawlers fill:#E3F2FD,stroke:#1E88E5,color:#000
    style ExecutePython fill:#FF9800,stroke:#F57C00,color:#fff
```

---

## 📂 Project Directory Structure

Your developer workspace and host storage directories are organized as follows:

```text
d:\Temp\automation\                # Developer Workspace
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git tracking safety filter
├── AI Job Search...json           # Main n8n Workflow JSON
├── Follow_Up_Automation.json      # Follow-Up Scheduler JSON
├── Dockerfile                     # Custom n8n + Python environment builder
├── docker-compose.yml             # Docker composition script
├── requirements.txt               # Python package dependencies
├── process_job.py                 # Main Python CRM worker
├── generate_workflow.py           # Programmatic n8n workflow compiler
├── inspect_execution.py           # sqlite n8n runtime inspector
└── test_process_job.py            # Unit testing suite

D:\AI Job Automation\              # Production Directory (Mounted on Host)
├── Resume/
│   └── Resume.txt                 # Input master text resume
├── Config/
│   └── config.json                # Job title & location preferences
├── Database/
│   └── jobs.db                    # SQLite CRM database
├── Excel/
│   └── JobTracker.xlsx            # Styled CRM Tracker Sheet (Navy Headers)
├── TailoredResume/
│   └── Resume_[Company]_[Role].*  # Tailored resumes (PDF and DOCX)
├── CoverLetters/
│   └── CoverLetter_[Comp]_[Role].*# Tailored Cover Letters & Cold Email drafts
└── Logs/
    └── automation.log             # Executable script activity log
```

---

## ⚙️ Setup & Execution Guide

### 1. Launch Services via Docker
Start Docker Desktop and initialize the container stack in your terminal:
```powershell
docker compose up -d
```

### 2. Configure Dashboard Credentials
Access **`http://localhost:5678`** in your browser and enter n8n account settings.
Import `AI Job Search_ Resume → Scored Job Matches.json` and configure credentials:
* **Google Gemini API**: Paste your Gemini API key.
* **Telegram Bot API**: Paste your Telegram bot token.
* **SMTP Node**: Enter your Gmail username and app password.

### 3. Execution
Place your master resume at `D:\AI Job Automation\Resume\Resume.txt` and job target parameters at `D:\AI Job Automation\Config\config.json`. Execute the manual run trigger inside the n8n editor, or let the schedule trigger run automatically.

---

## 🧪 Automated Testing
Verify the backend script modules locally using Python's standard `unittest` framework:
```powershell
.\.venv\Scripts\python.exe -m unittest test_process_job.py
```
This tests:
- SQLite database migrations & table creation.
- File and folder naming sanitization.
- FPDF2 Unicode/Latin-1 encoding crash sanitizers.
- DB profile and job CRUD transactions.

---

🏆 **Milestone Output**: Created and verified under recruitment requirements for [Sadique721](https://github.com/Sadique721).

<!-- ========== FOOTER WAVE ANIMATION ========== -->
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:22d3ee,100:8b5cf6&height=120&section=footer&width=100%">
</p>
