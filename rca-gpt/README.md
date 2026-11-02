# 🔍 RCA-GPT

**AI-Powered Root Cause Analysis for Support Engineers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automatically detect, classify, and analyze production incidents using machine learning. Find similar historical incidents, discover recurring patterns, and get AI-powered resolution suggestions.

![RCA-GPT Dashboard](docs/images/dashboard.png)

---

## 🎯 **What is RCA-GPT?**

RCA-GPT is an open-source incident management system that helps engineering teams:

- 🤖 **Automatically classify incidents** using ML (TF-IDF + Logistic Regression)
- 🔍 **Find similar historical incidents** and their resolutions
- 🔗 **Detect recurring patterns** (e.g., "Auth Error → Timeout → DB Error")
- 🕐 **Analyze timelines** to find the "original sin" that triggered cascades
- 📊 **Visualize trends** with an interactive Streamlit dashboard
- 💾 **Never lose context** - stores incidents with surrounding logs in SQLite

Unlike commercial tools (Datadog, PagerDuty), RCA-GPT is:
- ✅ **100% Free & Open Source**
- ✅ **Runs locally** (no vendor lock-in)
- ✅ **No LLM costs** (uses classical ML)
- ✅ **Privacy-first** (your data stays on your machine)

---

## 🚀 **Quick Start**

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/rca-gpt.git
cd rca-gpt

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Generate test data
python scripts/generate_test_incidents.py --count 100
python scripts/generate_cascade_patterns.py

# Train ML model
python -m rca_gpt.cli train

# Start monitoring
python -m rca_gpt.cli monitor
```

### Launch Dashboard
```bash
streamlit run dashboard.py
```

Open browser to `http://localhost:8501`

---

## 📊 **Features**

### 1️⃣ **Incident Classification**

Train ML classifier on your incident types:
```bash
# Add labeled data to data/training/training_data.csv
# Format: level,timestamp,message,incident_type

python -m rca_gpt.cli train
```

**Supported incident types:**
- Auth Error
- Timeout
- DB Error
- Network Error
- Custom types (add your own!)

### 2️⃣ **Similar Incident Matching**

Find incidents similar to current issues:
```bash
python -m rca_gpt.cli similar "Connection timeout"
```

**Output:**
```
🔍 Found 3 similar incident(s):

1. Incident #47 (94% similar)
   Type: Timeout
   Message: Connection timeout - retry failed
   Occurrences: 12
   ✅ Resolution: Increased connection pool size from 10 to 50
```

### 3️⃣ **Pattern Detection**

Discover recurring incident cascades:
```bash
python -m rca_gpt.cli patterns --days 30
```

**Output:**
```
🔍 Found 4 recurring pattern(s):

1. Auth Error → Timeout → DB Error
   Occurrences: 8
   Avg cascade time: 180s
```

### 4️⃣ **Timeline Analysis**

See what happened before/after incidents:
```bash
python -m rca_gpt.cli timeline 42 --before 10 --after 5
```

**Output:**
```
🕐 Timeline for Incident #42

🔍 ORIGINAL SIN: -8.3 min before [ERROR] DB connection pool exhausted

📋 Events:
  -8.3min [ERROR] DB connection pool exhausted
  -5.1min [WARN]  Slow query detected
  -2.4min [ERROR] Auth service timeout
  🎯 0.0min [ERROR] API Gateway 503 errors
  +1.2min [WARN]  Auto-scaling triggered
```

### 5️⃣ **Interactive Dashboard**

Visual interface with 4 pages:

- **📊 Dashboard** - Summary stats, top incidents, trends
- **🔍 Incident Explorer** - Search and browse incidents
- **🔗 Pattern Analysis** - Visualize cascading failures
- **🕐 Timeline Viewer** - Deep-dive into specific incidents

---

## 🛠️ **CLI Commands**

### Data Management
```bash
python -m rca_gpt.cli parse              # Parse logs to CSV
python -m rca_gpt.cli train              # Train ML model
python -m rca_gpt.cli predict "message"  # Classify single message
```

### Monitoring
```bash
python -m rca_gpt.cli monitor           # Start continuous monitoring
python -m rca_gpt.cli monitor --once    # Single check
```

### Incident Queries
```bash
python -m rca_gpt.cli history --days 7          # Recent incidents
python -m rca_gpt.cli show 42 --verbose         # Detailed view
python -m rca_gpt.cli stats --days 30 --top 10  # Statistics
python -m rca_gpt.cli search "timeout"          # Search incidents
```

### Analysis
```bash
python -m rca_gpt.cli similar "error message"   # Find similar
python -m rca_gpt.cli patterns --days 30        # Mine patterns
python -m rca_gpt.cli timeline 42               # Show timeline
```

### Resolution Tracking
```bash
python -m rca_gpt.cli resolve 15 "Fixed by restarting Redis" --by john_doe
```

### Export
```bash
python -m rca_gpt.cli export --days 7 -o report.json --include-occurrences
```

---

## 📁 **Project Structure**
```
rca-gpt/
├── rca_gpt/              # Core Python package
│   ├── cli.py           # Command-line interface
│   ├── parser.py        # Log parsing
│   ├── trainer.py       # ML training
│   ├── predictor.py     # Classification
│   ├── monitor.py       # Real-time monitoring
│   ├── similarity.py    # Similar incident matching
│   ├── patterns.py      # Pattern mining
│   ├── timeline.py      # Timeline analysis
│   └── db/
│       ├── models.py    # SQLAlchemy models
│       ├── manager.py   # Database operations
│       └── backup.py    # Backup utilities
├── config/
│   └── config.yaml      # Configuration
├── data/
│   ├── raw/            # Auto-generated logs
│   ├── training/       # Labeled training data
│   └── incidents.db    # SQLite database
├── models/             # Saved ML models
├── bash/               # Log generation scripts
├── scripts/            # Utility scripts
├── tests/              # Unit tests
├── dashboard.py        # Streamlit dashboard
└── docs/               # Documentation
```

---

## ⚙️ **Configuration**

Edit `config/config.yaml`:
```yaml
monitoring:
  check_interval_seconds: 60
  error_threshold: 3
  
database:
  path: data/incidents.db
  
ml:
  confidence_threshold: 0.7
```

---

## 🧪 **Development**

### Run Tests
```bash
python -m unittest discover tests/
```

### Generate Test Data
```bash
python scripts/generate_test_incidents.py --count 200
python scripts/generate_cascade_patterns.py
```

### Code Style
```bash
black rca_gpt/
flake8 rca_gpt/
```

---

## 🐳 **Docker**
```bash
# Build
docker build -t rca-gpt .

# Run
docker run -p 8501:8501 -v $(pwd)/data:/app/data rca-gpt
```

---

## 📖 **Documentation**

- [Database Schema](docs/database.md)
- [Adding Custom Incident Types](docs/custom_types.md)
- [Integration Guide](docs/integration.md)
- [API Reference](docs/api.md)

---

## 🗺️ **Roadmap**

- [x] Log parsing and storage
- [x] ML-based classification
- [x] Incident database with deduplication
- [x] Similar incident matching
- [x] Pattern mining
- [x] Timeline analysis
- [x] Streamlit dashboard
- [ ] Slack/Email alerting
- [ ] Jira integration
- [ ] Runbook suggestions (GPT-powered)
- [ ] Multi-tenant support
- [ ] Prometheus/Grafana integration

---

## 🤝 **Contributing**

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 **Author**

**Sai Sampath Ayalasomayajula**

Built to automate root cause analysis and help engineering teams resolve incidents faster.

---

## 🙏 **Acknowledgments**

- Inspired by real-world production support challenges
- Built with scikit-learn, SQLAlchemy, and Streamlit
- No LLMs harmed in the making of this project

---

## 📈 **Stats**

- **Lines of Code:** ~3,000
- **Test Coverage:** 85%
- **Dependencies:** 6 core libraries
- **Database Size:** <1MB for 1000+ incidents

---

## ⭐ **Star History**

If this project helps you, please star it on GitHub!
```
git clone https://github.com/yourusername/rca-gpt.git
cd rca-gpt
# Start contributing!
```

---

**Made with ❤️ and ☕ for support engineers everywhere**