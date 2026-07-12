import json
import os

def get_main_workflow():
    nodes = [
        # 1. Triggers & Config Load
        {
            "parameters": {},
            "id": "manual-trigger-id",
            "name": "Manual Test",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 0]
        },
        {
            "parameters": {
                "rule": {
                    "interval": [
                        {
                            "field": "days"
                        }
                    ]
                }
            },
            "id": "schedule-trigger-id",
            "name": "Schedule Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 160]
        },
        {
            "parameters": {
                "jsCode": """const fs = require('fs');
const path = require('path');
let config = {};
try {
  const dataDir = process.env.DATA_DIR || (process.platform === 'win32' ? 'D:/AI Job Automation' : '/data');
  const configPath = path.join(dataDir, 'Config/config.json');
  if (fs.existsSync(configPath)) {
    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
} catch (e) {}

// Set sensible defaults if file is missing
if (!config.targetTitles) config.targetTitles = ["Java Backend Engineer", "Spring Boot Developer", "Java Developer", "Backend Developer", "SDE-1", "Software Engineer"];
if (!config.locations) config.locations = ["India", "Remote"];
if (config.remoteOnly === undefined) config.remoteOnly = false;
if (!config.maxJobsPerRun) config.maxJobsPerRun = 25;
if (!config.postedWithinDays) config.postedWithinDays = 7;
if (!config.minMatchScore) config.minMatchScore = 50;
if (!config.excludeCompanies) config.excludeCompanies = [];

return [{ json: config }];"""
            },
            "id": "load-config-id",
            "name": "Load Config",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [200, 80]
        },
        {
            "parameters": {
                "jsCode": """const fs = require('fs');
const path = require('path');
const config = $('Load Config').first().json;
const input = $input.first()?.json || {};

// Load resume text
let resumeText = input.resumeText || input.Resume || "";
if (!resumeText) {
  try {
    const dataDir = process.env.DATA_DIR || (process.platform === 'win32' ? 'D:/AI Job Automation' : '/data');
    const resumePath = path.join(dataDir, "Resume/Resume.txt");
    if (fs.existsSync(resumePath)) {
      resumeText = fs.readFileSync(resumePath, 'utf8');
    }
  } catch (e) {}
}

if (!resumeText) {
  resumeText = "Md Sadique Amin. Email: mdsadiqueamin721786@gmail.com. Phone: +91 9318302850. Java Backend Engineer specializing in Spring Boot, Kafka, MySQL, and Docker.";
}

return [{
  json: {
    resumeText,
    config
  }
}];"""
            },
            "id": "parse-input-params-id",
            "name": "Parse Input Params",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [400, 80]
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Job search pipeline started.",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-start-id",
            "name": "Telegram: Workflow Started",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [600, 80],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        # 2. AI Parse Resume
        {
            "parameters": {
                "modelId": {
                    "__rl": True,
                    "mode": "id",
                    "value": "={{ $env.OLLAMA_MODEL || 'qwen2.5:7b-instruct' }}"
                },
                "messages": {
                    "values": [
                        {
                            "content": "=Extract the following from this resume text and return ONLY valid JSON (no markdown, no commentary) with this exact schema: {\"name\": \"string\", \"email\": \"string\", \"phone\": \"string\", \"skills\": [\"string\"], \"programmingLanguages\": [\"string\"], \"frameworks\": [\"string\"], \"libraries\": [\"string\"], \"databases\": [\"string\"], \"cloudPlatforms\": [\"string\"], \"aiSkills\": [\"string\"], \"devOpsSkills\": [\"string\"], \"yearsExperience\": number, \"education\": [\"string\"], \"projects\": [\"string\"], \"certifications\": [\"string\"], \"keywords\": [\"string\"], \"github\": \"string\", \"linkedin\": \"string\", \"summary\": \"string\"}.\n\nResume text:\n{{ $json.resumeText }}"
                        }
                    ]
                },
                "options": {
                    "system": "You are a precise resume-parsing engine for a recruitment automation system. Always respond with a single valid JSON object matching the requested schema and nothing else.",
                    "num_predict": 2000,
                    "temperature": 0,
                    "format": "json"
                }
            },
            "id": "ai-parse-resume-id",
            "name": "AI Parse Resume",
            "type": "@n8n/n8n-nodes-langchain.ollama",
            "typeVersion": 1,
            "position": [800, 80],
            "retryOnFail": True,
            "maxRetries": 3,
            "delayBetweenRetries": 10000,
            "credentials": {
                "ollamaApi": {
                    "id": "ollama-local-cred",
                    "name": "Local Ollama Account"
                }
            }
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Resume parsed successfully. Candidate: <b>{{ $json.name }}</b>",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-resume-parsed-id",
            "name": "Telegram: Resume Analysed",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [1000, 80],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        {
            "parameters": {
                "jsCode": """const config = $('Load Config').first().json;
const aiRaw = $input.first().json.text || $input.first().json.output || '';

function extractJson(text) {
  const cleaned = String(text).replace(/```json/gi, '').replace(/```/g, '').trim();
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start === -1 || end === -1) return {};
  try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) { return {}; }
}

const parsed = extractJson(aiRaw);
const candidate = {
  name: parsed.name || "Md Sadique Amin",
  email: parsed.email || "mdsadiqueamin721786@gmail.com",
  phone: parsed.phone || "+91 9318302850",
  skills: Array.isArray(parsed.skills) ? parsed.skills : [],
  programmingLanguages: Array.isArray(parsed.programmingLanguages) ? parsed.programmingLanguages : [],
  frameworks: Array.isArray(parsed.frameworks) ? parsed.frameworks : [],
  libraries: Array.isArray(parsed.libraries) ? parsed.libraries : [],
  databases: Array.isArray(parsed.databases) ? parsed.databases : [],
  cloudPlatforms: Array.isArray(parsed.cloudPlatforms) ? parsed.cloudPlatforms : [],
  aiSkills: Array.isArray(parsed.aiSkills) ? parsed.aiSkills : [],
  devOpsSkills: Array.isArray(parsed.devOpsSkills) ? parsed.devOpsSkills : [],
  yearsExperience: parsed.yearsExperience || 0,
  education: Array.isArray(parsed.education) ? parsed.education : [],
  topProjects: Array.isArray(parsed.projects) ? parsed.projects : [],
  certifications: Array.isArray(parsed.certifications) ? parsed.certifications : [],
  keywords: Array.isArray(parsed.keywords) ? parsed.keywords : [],
  github: parsed.github || 'https://github.com/sadiqueamin',
  linkedin: parsed.linkedin || 'https://linkedin.com/in/md-sadique-amin',
  summary: parsed.summary || 'Java Backend Engineer & Spring Boot Developer.',
  targetTitles: config.targetTitles || [],
  locations: config.locations || [],
  remoteOnly: config.remoteOnly === true,
  postedWithinDays: config.postedWithinDays || 7,
  minMatchScore: config.minMatchScore || 50,
  excludeCompanies: config.excludeCompanies || [],
  maxJobsPerRun: config.maxJobsPerRun || 25
};

return [{ json: candidate }];"""
            },
            "id": "parse-candidate-profile-id",
            "name": "Parse Candidate Profile",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1200, 80]
        },
        # 3. Crawler Nodes (Resilient + Retries)
        {
            "parameters": {
                "url": "https://remoteok.com/api",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {
                            "name": "User-Agent",
                            "value": "Mozilla/5.0 (compatible; JobSearchAutomation/1.0)"
                        }
                    ]
                },
                "options": {}
            },
            "id": "remoteok-fetch-id",
            "name": "Fetch RemoteOK Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, -400],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "loose",
                        "version": 1
                    },
                    "conditions": [
                        {
                            "leftValue": "={{ $json.id }}",
                            "operator": {
                                "type": "string",
                                "operation": "notEmpty"
                            },
                            "rightValue": ""
                        }
                    ],
                    "combinator": "and"
                },
                "options": {}
            },
            "id": "remoteok-filter-id",
            "name": "Filter Valid RemoteOK Rows",
            "type": "n8n-nodes-base.filter",
            "typeVersion": 2.3,
            "position": [1650, -400]
        },
        {
            "parameters": {
                "assignments": {
                    "assignments": [
                        {"id": "n1", "name": "title", "value": "={{ $json.position }}", "type": "string"},
                        {"id": "n2", "name": "company", "value": "={{ $json.company }}", "type": "string"},
                        {"id": "n3", "name": "jobLocation", "value": "={{ $json.location }}", "type": "string"},
                        {"id": "n4", "name": "jobUrl", "value": "={{ $json.url }}", "type": "string"},
                        {"id": "n5", "name": "source", "value": "RemoteOK", "type": "string"},
                        {"id": "n6", "name": "description", "value": "={{ $json.description }}", "type": "string"},
                        {"id": "n7", "name": "tags", "value": "={{ Array.isArray($json.tags) ? $json.tags.join(\", \") : \"\" }}", "type": "string"},
                        {"id": "n8", "name": "created", "value": "={{ new Date($json.date).toISOString() }}", "type": "string"}
                    ]
                },
                "options": {}
            },
            "id": "remoteok-normalize-id",
            "name": "Normalize RemoteOK Job",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [1850, -400]
        },
        {
            "parameters": {
                "url": "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true",
                "options": {}
            },
            "id": "greenhouse-fetch-id",
            "name": "Fetch Greenhouse Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, -250],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.jobs || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: "Stripe",
    jobLocation: j.location?.name || "Remote",
    jobUrl: j.absolute_url || "",
    source: "Greenhouse (Stripe)",
    description: j.content || "",
    tags: "",
    created: j.updated_at || ""
  }
}));"""
            },
            "id": "greenhouse-normalize-id",
            "name": "Normalize Greenhouse Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, -250]
        },
        {
            "parameters": {
                "url": "https://api.lever.co/v0/postings/lever?mode=json",
                "options": {}
            },
            "id": "lever-fetch-id",
            "name": "Fetch Lever Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, -100],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.all().map(i => i?.json).filter(Boolean); } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: "Lever",
    jobLocation: j.categories?.location || "Remote",
    jobUrl: j.hostedUrl || "",
    source: "Lever (Lever)",
    description: j.description || "",
    tags: j.categories?.team || "",
    created: j.createdAt ? new Date(j.createdAt).toISOString() : ""
  }
}));"""
            },
            "id": "lever-normalize-id",
            "name": "Normalize Lever Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, -100]
        },
        {
            "parameters": {
                "url": "https://api.ashbyhq.com/v1/jobs?boardToken=sentry",
                "options": {}
            },
            "id": "ashby-fetch-id",
            "name": "Fetch Ashby Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 50],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.jobs || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: "Sentry",
    jobLocation: j.location || "Remote",
    jobUrl: j.jobUrl || "",
    source: "Ashby (Sentry)",
    description: j.description || "",
    tags: "",
    created: j.publishedAt || ""
  }
}));"""
            },
            "id": "ashby-normalize-id",
            "name": "Normalize Ashby Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 50]
        },
        # New sources
        {
            "parameters": {
                "url": "=https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={{ $env.ADZUNA_APP_ID }}&app_key={{ $env.ADZUNA_API_KEY }}&what={{ encodeURIComponent($('Parse Candidate Profile').first().json.targetTitles.join(' OR ')) }}&results_per_page=20&content-type=application/json",
                "options": {}
            },
            "id": "adzuna-fetch-id",
            "name": "Fetch Adzuna Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 200],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.results || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: j.company?.display_name || "Unknown",
    jobLocation: j.location?.display_name || "India",
    jobUrl: j.redirect_url || "",
    source: "Adzuna",
    description: j.description || "",
    tags: (j.category?.label || "") + ", " + (j.category?.tag || ""),
    created: j.created || ""
  }
}));"""
            },
            "id": "adzuna-normalize-id",
            "name": "Normalize Adzuna Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 200]
        },
        {
            "parameters": {
                "method": "POST",
                "url": "=https://jooble.org/api/{{ $env.JOOBLE_API_KEY }}",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "keywords", "value": "={{ $('Parse Candidate Profile').first().json.targetTitles.join(' OR ') }}"},
                        {"name": "location", "value": "India"}
                    ]
                },
                "options": {}
            },
            "id": "jooble-fetch-id",
            "name": "Fetch Jooble Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 350],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.jobs || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: j.company || "Unknown",
    jobLocation: j.location || "India",
    jobUrl: j.link || "",
    source: "Jooble",
    description: j.snippet || "",
    tags: "",
    created: j.updated ? new Date(j.updated).toISOString() : ""
  }
}));"""
            },
            "id": "jooble-normalize-id",
            "name": "Normalize Jooble Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 350]
        },
        {
            "parameters": {
                "url": "=https://jsearch.p.rapidapi.com/search?query={{ encodeURIComponent($('Parse Candidate Profile').first().json.targetTitles.join(' OR ') + ' in India') }}&num_pages=1",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "X-RapidAPI-Key", "value": "={{ $env.JSEARCH_API_KEY }}"},
                        {"name": "X-RapidAPI-Host", "value": "jsearch.p.rapidapi.com"}
                    ]
                },
                "options": {}
            },
            "id": "jsearch-fetch-id",
            "name": "Fetch JSearch Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 500],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.data || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.job_title || "",
    company: j.employer_name || "Unknown",
    jobLocation: j.job_city || j.job_country || "India",
    jobUrl: j.job_apply_link || "",
    source: "JSearch",
    description: j.job_description || "",
    tags: "",
    created: j.job_posted_at_datetime_utc || ""
  }
}));"""
            },
            "id": "jsearch-normalize-id",
            "name": "Normalize JSearch Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 500]
        },
        {
            "parameters": {
                "url": "https://api.smartrecruiters.com/v1/companies/razorpay/postings",
                "options": {}
            },
            "id": "smartrecruiters-fetch-id",
            "name": "Fetch SmartRecruiters Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 650],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.content || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.name || "",
    company: "Razorpay",
    jobLocation: j.location?.city || "Remote",
    jobUrl: `https://careers.smartrecruiters.com/Razorpay/${j.id}`,
    source: "SmartRecruiters (Razorpay)",
    description: j.customField?.find(f => f.fieldId === 'description')?.value || j.name || "",
    tags: j.department?.label || "",
    created: j.releasedDate || ""
  }
}));"""
            },
            "id": "smartrecruiters-normalize-id",
            "name": "Normalize SmartRecruiters Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 650]
        },
        {
            "parameters": {
                "url": "https://wetransfer.recruitee.com/api/2/jobs",
                "options": {}
            },
            "id": "recruitee-fetch-id",
            "name": "Fetch Recruitee Jobs",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.4,
            "position": [1450, 800],
            "continueOnFail": True,
            "retryOnFail": True,
            "maxRetries": 2,
            "delayBetweenRetries": 5000
        },
        {
            "parameters": {
                "jsCode": """let input = [];
try { input = $input.first()?.json?.jobs || []; } catch(e) {}
return input.map(j => ({
  json: {
    title: j.title || "",
    company: "WeTransfer",
    jobLocation: j.location || "Remote",
    jobUrl: j.careers_url || "",
    source: "Recruitee (WeTransfer)",
    description: j.description || "",
    tags: j.tags?.join(", ") || "",
    created: j.published_at || ""
  }
}));"""
            },
            "id": "recruitee-normalize-id",
            "name": "Normalize Recruitee Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1650, 800]
        },
        # 4. Central JS Merge and Filter
        {
            "parameters": {
                "jsCode": """const candidate = $('Parse Candidate Profile').first()?.json || {};
const locations = (candidate.locations || []).map(l => String(l).toLowerCase());
const excludeCompanies = (candidate.excludeCompanies || []).map(c => String(c).toLowerCase());
const postedWithinDays = Number(candidate.postedWithinDays) || 7;
const remoteOnly = candidate.remoteOnly === true;

let rawJobs = [];

const sources = [
  { name: 'RemoteOK', node: 'Normalize RemoteOK Job' },
  { name: 'Greenhouse', node: 'Normalize Greenhouse Jobs' },
  { name: 'Lever', node: 'Normalize Lever Jobs' },
  { name: 'Ashby', node: 'Normalize Ashby Jobs' },
  { name: 'Adzuna', node: 'Normalize Adzuna Jobs' },
  { name: 'Jooble', node: 'Normalize Jooble Jobs' },
  { name: 'JSearch', node: 'Normalize JSearch Jobs' },
  { name: 'SmartRecruiters', node: 'Normalize SmartRecruiters Jobs' },
  { name: 'Recruitee', node: 'Normalize Recruitee Jobs' }
];

const counts = {};

for (const src of sources) {
  let items = [];
  try {
    const allItems = $(src.node).all();
    if (Array.isArray(allItems)) {
      items = allItems.map(i => i?.json).filter(Boolean);
    }
  } catch (e) {}
  counts[src.name] = items.length;
  rawJobs = rawJobs.concat(items);
}

// 1. Deduplicate by Job URL in this run
const uniqueJobsMap = new Map();
for (const job of rawJobs) {
  if (job.jobUrl) {
    uniqueJobsMap.set(job.jobUrl, job);
  }
}

const uniqueJobs = Array.from(uniqueJobsMap.values());

// 2. Apply Filters (Exclusions, Date limits, Locations, Title Match)
const now = new Date();
const filteredJobs = uniqueJobs.filter(j => {
  // Check company exclusion
  const comp = String(j.company || '').toLowerCase();
  if (excludeCompanies.some(ex => comp.includes(ex))) return false;
  
  // Check Date Limits
  if (j.created) {
    const createdDate = new Date(j.created);
    if (!isNaN(createdDate.getTime())) {
      const diffTime = Math.abs(now - createdDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > postedWithinDays) return false;
    }
  }
  
  // Check Title
  const title = String(j.title || '').toLowerCase();
  const targetTitles = (candidate.targetTitles || []).map(t => String(t).toLowerCase());
  const matchesTitle = targetTitles.length === 0 || targetTitles.some(t => title.includes(t));
  if (!matchesTitle) return false;
  
  // Check Location
  const loc = String(j.jobLocation || '').toLowerCase();
  if (remoteOnly) {
    const isRemote = loc.includes('remote') || j.source === 'RemoteOK';
    if (!isRemote) return false;
  }
  
  if (locations.length > 0) {
    const matchesLoc = locations.some(l => loc.includes(l) || (l === 'remote' && loc.includes('remote')));
    if (!matchesLoc) return false;
  }
  
  return true;
});

return [{
  json: {
    jobs: filteredJobs,
    counts: counts,
    totalDiscovered: rawJobs.length,
    totalFiltered: filteredJobs.length
  }
}];"""
            },
            "id": "merge-filter-jobs-id",
            "name": "Merge & Filter Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2100, 80]
        },
        # 5. Telegram Count Summary Node
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": """=📊 <b>Job Crawling Summary</b>
- RemoteOK: {{ $json.counts.RemoteOK }}
- Greenhouse: {{ $json.counts.Greenhouse }}
- Lever: {{ $json.counts.Lever }}
- Ashby: {{ $json.counts.Ashby }}
- Adzuna: {{ $json.counts.Adzuna }}
- Jooble: {{ $json.counts.Jooble }}
- JSearch: {{ $json.counts.JSearch }}
- SmartRecruiters: {{ $json.counts.SmartRecruiters }}
- Recruitee: {{ $json.counts.Recruitee }}

<b>Total Discovered:</b> {{ $json.totalDiscovered }}
<b>Filtered (Criteria Fit):</b> {{ $json.totalFiltered }}""",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-jobs-found-id",
            "name": "Telegram: Jobs Found",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [2300, -80],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        # 6. Split List
        {
            "parameters": {
                "jsCode": """return $input.first().json.jobs.map(j => ({ json: j }));"""
            },
            "id": "split-jobs-list-id",
            "name": "Split Jobs List",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2900, 80]
        },
        # 7. SQLite URL Deduplication Node (Small command line call)
        {
            "parameters": {
                "command": """={{ $env.PYTHON_CMD || 'python' }} -c "import sqlite3, json, os; db = os.path.join(os.environ.get('DATA_DIR', '/data'), 'Database/jobs.db'); conn=sqlite3.connect(db); c=conn.cursor(); c.execute('SELECT job_url FROM jobs'); urls=[r[0] for r in c.fetchall()]; conn.close(); print(json.dumps(urls))" """
            },
            "id": "get-existing-urls-id",
            "name": "Get Existing URLs",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [2300, 240]
        },
        {
            "parameters": {
                "jsCode": """const allJobs = $('Merge & Filter Jobs').first().json.jobs || [];
let existingUrls = [];
try {
  existingUrls = JSON.parse($('Get Existing URLs').first().json.stdout);
} catch (e) {}
const existingSet = new Set(existingUrls);
const newJobs = allJobs.filter(j => !existingSet.has(j.jobUrl));
return [{ json: { jobs: newJobs } }];"""
            },
            "id": "filter-existing-jobs-id",
            "name": "Filter Existing Jobs",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [2500, 80]
        },
        # 8. Check if New Jobs Exist
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "loose",
                        "version": 1
                    },
                    "conditions": [
                        {
                            "leftValue": "={{ $json.jobs.length }}",
                            "operator": {
                                "type": "number",
                                "operation": "gt"
                            },
                            "rightValue": 0
                        }
                    ],
                    "combinator": "and"
                },
                "options": {}
            },
            "id": "check-new-jobs-id",
            "name": "Check New Jobs Exist",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [2700, 80]
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "<b>[Job Automation]</b> No new jobs found in today's search.",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-no-jobs-id",
            "name": "Telegram: No Jobs Found",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [2900, -20],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        # 9. Score & Rank Jobs Node (Gemini Rubric Evaluation)
        {
            "parameters": {
                "modelId": {
                    "__rl": True,
                    "mode": "id",
                    "value": "={{ $env.OLLAMA_MODEL || 'qwen2.5:7b-instruct' }}"
                },
                "messages": {
                    "values": [
                        {
                            "content": "=Candidate Skills: {{ $('Parse Candidate Profile').first().json.skills.join(', ') }}\nCandidate Experience: {{ $('Parse Candidate Profile').first().json.yearsExperience }} years\nCandidate Summary: {{ $('Parse Candidate Profile').first().json.summary }}\n\nJob Title: {{ $json.title }}\nCompany: {{ $json.company }}\nJob Location: {{ $json.jobLocation }}\nJob Description: {{ $json.description }}\n\nEvaluate the fit of the candidate for this job using the following weighted rubric:\n1. Skills Overlap (40%): Fit between candidate skills and job requirements.\n2. Experience Match (20%): Fit between candidate years of experience and job needs.\n3. Location/Remote Fit (20%): Remote alignment and location preferences.\n4. Role Fit (20%): Title alignment.\n\nCalculate a final score (0-100) using this rubric. Identify the skill gap (skills in job but missing in resume) and contact email if mentioned.\n\nReturn ONLY a valid JSON object matching this schema:\n{\n  \"matchScore\": number,\n  \"matchedSkills\": \"string list of matching skills\",\n  \"skillGap\": \"string list of missing skills\",\n  \"experienceMatch\": \"High / Medium / Low\",\n  \"locationMatch\": \"Yes / No\",\n  \"remoteMatch\": \"Yes / No\",\n  \"salaryMatch\": \"N/A or detail\",\n  \"priorityScore\": number,\n  \"recommendation\": \"Apply / Skip / Review\",\n  \"matchSummary\": \"1-2 sentence summary of fit\",\n  \"contactEmail\": \"email address if found in job description, otherwise blank\"\n}"
                        }
                    ]
                },
                "options": {
                    "system": "You are a recruitment screening engine. Evaluate candidate fit strictly according to the provided rubric and return ONLY valid JSON.",
                    "num_predict": 1000,
                    "temperature": 0.1,
                    "format": "json"
                }
            },
            "id": "score-rank-jobs-id",
            "name": "Score & Rank Jobs",
            "type": "@n8n/n8n-nodes-langchain.ollama",
            "typeVersion": 1,
            "position": [2900, 180],
            "retryOnFail": True,
            "maxRetries": 3,
            "delayBetweenRetries": 10000,
            "credentials": {
                "ollamaApi": {
                    "id": "ollama-local-cred",
                    "name": "Local Ollama Account"
                }
            }
        },
        {
            "parameters": {
                "jsCode": "return $input.all().map(item => {\n  const job = item.json;\n  function extractJson(text) {\n    const cleaned = String(text).replace(/```json/gi, '').replace(/```/g, '').trim();\n    const start = cleaned.indexOf('{');\n    const end = cleaned.lastIndexOf('}');\n    if (start === -1 || end === -1) return {};\n    try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) { return {}; }\n  }\n  const parsed = extractJson(job.text || job.output || '');\n  const originalJob = $('Split Jobs List').all()[item.index].json;\n  return {\n    json: {\n      ...originalJob,\n      matchScore: parsed.matchScore || 0,\n      matchedSkills: parsed.matchedSkills || '',\n      tailored: parsed\n    }\n  };\n});"
            },
            "id": "parse-scoring-results-id",
            "name": "Parse Scoring Results",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [3100, 180]
        },
        # 10. Filter by Minimum Match Score
        {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "loose",
                        "version": 1
                    },
                    "conditions": [
                        {
                            "leftValue": "={{ $json.matchScore }}",
                            "operator": {
                                "type": "number",
                                "operation": "gte"
                            },
                            "rightValue": "={{ $('Parse Candidate Profile').first().json.minMatchScore }}"
                        }
                    ],
                    "combinator": "and"
                },
                "options": {}
            },
            "id": "filter-min-score-id",
            "name": "Filter By Minimum Score",
            "type": "n8n-nodes-base.filter",
            "typeVersion": 2.3,
            "position": [3300, 180]
        },
        # 11. Limit Node (maxJobsPerRun)
        {
            "parameters": {
                "maxItems": "={{ $('Load Config').first().json.maxJobsPerRun || 25 }}"
            },
            "id": "limit-jobs-id",
            "name": "Limit Jobs per Run",
            "type": "n8n-nodes-base.limit",
            "typeVersion": 1,
            "position": [3500, 180]
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Found <b>{{ $input.all().length }}</b> high-match new jobs (>= {{ $('Parse Candidate Profile').first().json.minMatchScore }}%). Starting tailoring...",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-high-match-id",
            "name": "Telegram: High Match Jobs",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [3700, 180],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        # 12. Loop Over High Match Jobs
        {
            "parameters": {
                "options": {}
            },
            "id": "loop-matched-jobs-id",
            "name": "Loop Over Matched Jobs",
            "type": "n8n-nodes-base.splitInBatches",
            "typeVersion": 3,
            "position": [3900, 180]
        },
        # 13. AI Tailor Application Notes
        {
            "parameters": {
                "modelId": {
                    "__rl": True,
                    "mode": "id",
                    "value": "={{ $env.OLLAMA_MODEL || 'qwen2.5:7b-instruct' }}"
                },
                "messages": {
                    "values": [
                        {
                            "content": "=Candidate Summary: {{ $('Parse Candidate Profile').first().json.summary }}\nCandidate Skills: {{ $('Parse Candidate Profile').first().json.skills.join(', ') }}\nCandidate Experience: {{ $('Parse Candidate Profile').first().json.yearsExperience }} years\n\nJob Title: {{ $json.title }}\nCompany: {{ $json.company }}\nJob Description: {{ $json.description }}\n\nTailor the candidate's resume highlights and draft cover letter components. Return ONLY JSON matching this schema:\n{\n  \"tailoredBullets\": [\"bullet 1\", \"bullet 2\", \"bullet 3\"],\n  \"coverLetterOpener\": \"cover letter opening paragraph\"\n}"
                        }
                    ]
                },
                "options": {
                    "system": "You are a career development coach. Create resume bullets and cover letter elements strictly tailored to this company and role.",
                    "num_predict": 1000,
                    "temperature": 0.4,
                    "format": "json"
                }
            },
            "id": "ai-tailor-application-notes-id",
            "name": "AI Tailor Application Notes",
            "type": "@n8n/n8n-nodes-langchain.ollama",
            "typeVersion": 1,
            "position": [4100, 50],
            "retryOnFail": True,
            "maxRetries": 3,
            "delayBetweenRetries": 10000,
            "credentials": {
                "ollamaApi": {
                    "id": "ollama-local-cred",
                    "name": "Local Ollama Account"
                }
            }
        },
        {
            "parameters": {
                "jsCode": """const currentJob = $('Loop Over Matched Jobs').item.json;
const aiRaw = $input.item.json.text || $input.item.json.output || "";

function extractJson(text) {
  const cleaned = String(text).replace(/```json/gi, '').replace(/```/g, '').trim();
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start === -1 || end === -1) return {};
  try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) { return {}; }
}

const tailoredData = extractJson(aiRaw);
const candidate = $('Parse Candidate Profile').first().json;

const combinedTailored = {
  ...currentJob.tailored,
  tailoredBullets: tailoredData.tailoredBullets || [],
  coverLetterOpener: tailoredData.coverLetterOpener || ""
};

return [{
  json: {
    candidate: candidate,
    job: currentJob,
    tailored: combinedTailored
  }
}];"""
            },
            "id": "build-crm-row-id",
            "name": "Build CRM Row",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [4300, 50]
        },
        # 14. Execute Local Python Processor
        {
            "parameters": {
                "command": "={{ $env.PYTHON_CMD || 'python' }} \"{{ $env.DATA_DIR || '/data' }}/Config/process_job.py\"",
                "sendStdin": True,
                "stdinProperty": "={{ JSON.stringify($json) }}"
            },
            "id": "execute-local-processor-id",
            "name": "Execute Local Processor",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [4500, 50]
        },
        # 15. Notifications
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Tailored resume and cover letter generated for <b>{{ $json.job.title }}</b> at <b>{{ $json.job.company }}</b>.\nPriority Match: <b>{{ $json.tailored.priorityScore }}</b>",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-resume-tailored-id",
            "name": "Telegram: Resume Tailored",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [4700, 50],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        {
            "parameters": {
                "fromEmail": "={{ $env.SMTP_USER }}",
                "toEmail": "={{ $env.SMTP_USER }}",
                "subject": "=Tailored Application Package: {{ $json.job.title }} at {{ $json.job.company }}",
                "html": "=Hi,<br><br>Here is your tailored application package. The files have been written on the host.<br><br><b>Cold Email Draft:</b><br><pre>Subject: Application for {{ $json.job.title }} - {{ $json.candidate.name.toUpperCase() }}\n\nDear Hiring Team at {{ $json.job.company }},\n\n{{ $json.tailored.coverLetterOpener }}\n\nBest regards,\n{{ $json.candidate.name }}</pre>",
                "options": {}
            },
            "id": "smtp-send-notification-id",
            "name": "SMTP: Send Notification",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2.1,
            "position": [4900, 50],
            "credentials": {
                "smtp": {
                    "id": "smtp-cred-id",
                    "name": "SMTP Account"
                }
            }
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Workflow execution completed. CRM updated and follow-ups scheduled.",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-workflow-finished-id",
            "name": "Telegram: Workflow Finished",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [4100, 300],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        # 16. Error Triggers
        {
            "parameters": {},
            "id": "error-trigger-id",
            "name": "Error Trigger",
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [0, 450]
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation] ERROR</b>: Node <code>{{ $json.execution.error.node.name }}</code> failed.<br>Message: <code>{{ $json.execution.error.message }}</code>",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-error-notifier-id",
            "name": "Telegram: Error Notifier",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [200, 400],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        },
        {
            "parameters": {
                "fromEmail": "={{ $env.SMTP_USER }}",
                "toEmail": "={{ $env.SMTP_USER }}",
                "subject": "=Workflow Alert: Automation Error",
                "html": "=Hi,<br><br>The job search workflow encountered an error at node <b>{{ $json.execution.error.node.name }}</b>.<br><br><b>Error Message:</b><br><pre>{{ $json.execution.error.message }}</pre>",
                "options": {}
            },
            "id": "smtp-error-notifier-id",
            "name": "SMTP: Error Notifier",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2.1,
            "position": [200, 520],
            "credentials": {
                "smtp": {
                    "id": "smtp-cred-id",
                    "name": "SMTP Account"
                }
            }
        }
    ]

    # Connections Mapping
    connections = {
        "Manual Test": {"main": [[{"node": "Load Config", "type": "main", "index": 0}]]},
        "Schedule Trigger": {"main": [[{"node": "Load Config", "type": "main", "index": 0}]]},
        "Load Config": {"main": [[{"node": "Parse Input Params", "type": "main", "index": 0}]]},
        "Parse Input Params": {"main": [[{"node": "Telegram: Workflow Started", "type": "main", "index": 0}]]},
        "Telegram: Workflow Started": {"main": [[{"node": "AI Parse Resume", "type": "main", "index": 0}]]},
        "AI Parse Resume": {"main": [[{"node": "Telegram: Resume Analysed", "type": "main", "index": 0}]]},
        "Telegram: Resume Analysed": {"main": [[{"node": "Parse Candidate Profile", "type": "main", "index": 0}]]},
        "Parse Candidate Profile": {
            "main": [[
                {"node": "Fetch RemoteOK Jobs", "type": "main", "index": 0},
                {"node": "Fetch Greenhouse Jobs", "type": "main", "index": 0},
                {"node": "Fetch Lever Jobs", "type": "main", "index": 0},
                {"node": "Fetch Ashby Jobs", "type": "main", "index": 0},
                {"node": "Fetch Adzuna Jobs", "type": "main", "index": 0},
                {"node": "Fetch Jooble Jobs", "type": "main", "index": 0},
                {"node": "Fetch JSearch Jobs", "type": "main", "index": 0},
                {"node": "Fetch SmartRecruiters Jobs", "type": "main", "index": 0},
                {"node": "Fetch Recruitee Jobs", "type": "main", "index": 0}
            ]]
        },
        # Crawler branches
        "Fetch RemoteOK Jobs": {"main": [[{"node": "Filter Valid RemoteOK Rows", "type": "main", "index": 0}]]},
        "Filter Valid RemoteOK Rows": {"main": [[{"node": "Normalize RemoteOK Job", "type": "main", "index": 0}]]},
        "Normalize RemoteOK Job": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Greenhouse Jobs": {"main": [[{"node": "Normalize Greenhouse Jobs", "type": "main", "index": 0}]]},
        "Normalize Greenhouse Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Lever Jobs": {"main": [[{"node": "Normalize Lever Jobs", "type": "main", "index": 0}]]},
        "Normalize Lever Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Ashby Jobs": {"main": [[{"node": "Normalize Ashby Jobs", "type": "main", "index": 0}]]},
        "Normalize Ashby Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Adzuna Jobs": {"main": [[{"node": "Normalize Adzuna Jobs", "type": "main", "index": 0}]]},
        "Normalize Adzuna Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Jooble Jobs": {"main": [[{"node": "Normalize Jooble Jobs", "type": "main", "index": 0}]]},
        "Normalize Jooble Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch JSearch Jobs": {"main": [[{"node": "Normalize JSearch Jobs", "type": "main", "index": 0}]]},
        "Normalize JSearch Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch SmartRecruiters Jobs": {"main": [[{"node": "Normalize SmartRecruiters Jobs", "type": "main", "index": 0}]]},
        "Normalize SmartRecruiters Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        "Fetch Recruitee Jobs": {"main": [[{"node": "Normalize Recruitee Jobs", "type": "main", "index": 0}]]},
        "Normalize Recruitee Jobs": {"main": [[{"node": "Merge & Filter Jobs", "type": "main", "index": 0}]]},
        
        # Post-Merge branch
        "Merge & Filter Jobs": {
            "main": [[
                {"node": "Telegram: Jobs Found", "type": "main", "index": 0},
                {"node": "Filter Existing Jobs", "type": "main", "index": 0}
            ]]
        },
        "Filter Existing Jobs": {"main": [[{"node": "Check New Jobs Exist", "type": "main", "index": 0}]]},
        "Check New Jobs Exist": {
            "main": [
                [{"node": "Split Jobs List", "type": "main", "index": 0}], # true
                [{"node": "Telegram: No Jobs Found", "type": "main", "index": 0}]  # false
            ]
        },
        "Split Jobs List": {"main": [[{"node": "Score & Rank Jobs", "type": "main", "index": 0}]]},
        "Score & Rank Jobs": {"main": [[{"node": "Parse Scoring Results", "type": "main", "index": 0}]]},
        "Parse Scoring Results": {"main": [[{"node": "Filter By Minimum Score", "type": "main", "index": 0}]]},
        "Filter By Minimum Score": {"main": [[{"node": "Limit Jobs per Run", "type": "main", "index": 0}]]},
        "Limit Jobs per Run": {"main": [[{"node": "Telegram: High Match Jobs", "type": "main", "index": 0}]]},
        "Telegram: High Match Jobs": {"main": [[{"node": "Loop Over Matched Jobs", "type": "main", "index": 0}]]},
        
        # Loop branch
        "Loop Over Matched Jobs": {
            "main": [
                [{"node": "Telegram: Workflow Finished", "type": "main", "index": 0}], # finished
                [{"node": "AI Tailor Application Notes", "type": "main", "index": 0}]  # next item
            ]
        },
        "AI Tailor Application Notes": {"main": [[{"node": "Build CRM Row", "type": "main", "index": 0}]]},
        "Build CRM Row": {"main": [[{"node": "Execute Local Processor", "type": "main", "index": 0}]]},
        "Execute Local Processor": {"main": [[{"node": "Telegram: Resume Tailored", "type": "main", "index": 0}]]},
        "Telegram: Resume Tailored": {"main": [[{"node": "SMTP: Send Notification", "type": "main", "index": 0}]]},
        "SMTP: Send Notification": {"main": [[{"node": "Loop Over Matched Jobs", "type": "main", "index": 0}]]},
        
        # Error Trigger branch
        "Error Trigger": {
            "main": [[
                {"node": "Telegram: Error Notifier", "type": "main", "index": 0},
                {"node": "SMTP: Error Notifier", "type": "main", "index": 0}
            ]]
        }
    }

    return {
        "name": "AI Job Search: Resume → Scored Job Matches",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
            "availableInMCP": True
        },
        "meta": {
            "aiBuilderAssisted": True,
            "builderVariant": "mcp"
        }
    }

def get_followup_workflow():
    nodes = [
        {
            "parameters": {
                "rule": {
                    "interval": [
                        {
                            "field": "days"
                        }
                    ]
                }
            },
            "id": "schedule-trigger-id",
            "name": "Schedule Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 0]
        },
        {
            "parameters": {
                "command": """={{ $env.PYTHON_CMD || 'python' }} -c "
import sqlite3, json, datetime, os
db = os.path.join(os.environ.get('DATA_DIR', '/data'), 'Database/jobs.db')
conn = sqlite3.connect(db)
cursor = conn.cursor()
today = datetime.datetime.now().strftime('%Y-%m-%d')
cursor.execute('''
    SELECT job_url, title, company, contact_email, follow_up_count 
    FROM jobs 
    WHERE status = 'Applied' 
      AND next_follow_up_date <= ? 
      AND follow_up_count < 2 
      AND contact_email IS NOT NULL 
      AND contact_email != ''
''', (today,))
cols = ['job_url', 'title', 'company', 'contact_email', 'follow_up_count']
rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
conn.close()
print(json.dumps(rows))
" """
            },
            "id": "get-follow-ups-id",
            "name": "Get Follow-Up Candidates",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [200, 0]
        },
        {
            "parameters": {
                "jsCode": "return JSON.parse($input.first().json.stdout).map(r => ({ json: r }));"
            },
            "id": "split-candidates-id",
            "name": "Split Candidates",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [400, 0]
        },
        {
            "parameters": {
                "fromEmail": "={{ $env.SMTP_USER }}",
                "toEmail": "={{ $json.contact_email }}",
                "ccEmail": "={{ $env.SMTP_USER }}",
                "subject": "=Following up on my application: {{ $json.title }} at {{ $json.company }}",
                "html": "=Dear Hiring Team at {{ $json.company }},<br><br>I hope this email finds you well.<br><br>I am following up on the application I submitted for the <b>{{ $json.title }}</b> position a few days ago.<br><br>I am very interested in this opportunity and wanted to confirm that my application materials were successfully received. Please let me know if you need any additional documents or details from my end.<br><br>Thank you for your time and consideration.<br><br>Sincerely,<br>Md Sadique Amin<br>mdsadiqueamin721786@gmail.com",
                "options": {}
            },
            "id": "smtp-followup-email-id",
            "name": "SMTP: Send Follow-up Email",
            "type": "n8n-nodes-base.emailSend",
            "typeVersion": 2.1,
            "position": [600, 0],
            "credentials": {
                "smtp": {
                    "id": "smtp-cred-id",
                    "name": "SMTP Account"
                }
            }
        },
        {
            "parameters": {
                "command": """={{ $env.PYTHON_CMD || 'python' }} -c "
import sys, json, sqlite3, datetime, os
payload = json.load(sys.stdin)
db = os.path.join(os.environ.get('DATA_DIR', '/data'), 'Database/jobs.db')
conn = sqlite3.connect(db)
cursor = conn.cursor()
today = datetime.datetime.now()
next_date = (today + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
cursor.execute('''
    UPDATE jobs 
    SET follow_up_count = follow_up_count + 1, 
        next_follow_up_date = ? 
    WHERE job_url = ?
''', (next_date, payload.get('job_url')))
conn.commit()
conn.close()
print('Updated')
" """,
                "sendStdin": True,
                "stdinProperty": "={{ JSON.stringify($json) }}"
            },
            "id": "update-followup-log-id",
            "name": "Update Follow-up Log",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [800, 0]
        },
        {
            "parameters": {
                "chatId": "={{ $env.N8N_TELEGRAM_CHAT_ID }}",
                "text": "=<b>[Job Automation]</b> Follow-up email sent to <b>{{ $json.company }}</b> ({{ $json.contact_email }}) for <b>{{ $json.title }}</b> (Follow-up #{{ $json.follow_up_count + 1 }}).",
                "additionalFields": {
                    "parse_mode": "HTML"
                }
            },
            "id": "telegram-followup-sent-id",
            "name": "Telegram: Followup Sent",
            "type": "n8n-nodes-base.telegram",
            "continueOnFail": True,
            "typeVersion": 1.2,
            "position": [1000, 0],
            "credentials": {
                "telegramApi": {
                    "id": "telegram-cred-id",
                    "name": "Telegram Bot Account"
                }
            }
        }
    ]

    connections = {
        "Schedule Trigger": {"main": [[{"node": "Get Follow-Up Candidates", "type": "main", "index": 0}]]},
        "Get Follow-Up Candidates": {"main": [[{"node": "Split Candidates", "type": "main", "index": 0}]]},
        "Split Candidates": {"main": [[{"node": "SMTP: Send Follow-up Email", "type": "main", "index": 0}]]},
        "SMTP: Send Follow-up Email": {"main": [[{"node": "Update Follow-up Log", "type": "main", "index": 0}]]},
        "Update Follow-up Log": {"main": [[{"node": "Telegram: Followup Sent", "type": "main", "index": 0}]]}
    }

    return {
        "name": "Follow-Up Automation",
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "binaryMode": "separate",
            "availableInMCP": True
        },
        "meta": {
            "aiBuilderAssisted": True,
            "builderVariant": "mcp"
        }
    }

def main():
    main_wf = get_main_workflow()
    followup_wf = get_followup_workflow()
    
    # Add top-level ID to prevent SQLite NOT NULL constraints during import
    main_wf["id"] = "1"
    followup_wf["id"] = "2"
    
    out_dir = os.path.dirname(__file__)
    main_path = os.path.join(out_dir, 'AI_Job_Search_Resume_Scored_Job_Matches.json')
    with open(main_path, 'w', encoding='utf-8') as f:
        json.dump(main_wf, f, indent=2, ensure_ascii=False)
        
    followup_path = os.path.join(out_dir, 'Follow_Up_Automation.json')
    with open(followup_path, 'w', encoding='utf-8') as f:
        json.dump(followup_wf, f, indent=2, ensure_ascii=False)

    print("Successfully generated n8n workflow files.")

if __name__ == '__main__':
    main()
