# Quick Start Guide

Get RCA-GPT running in 5 minutes.

## Prerequisites

- Python 3.8+
- pip
- 100MB free disk space

## Installation
```bash
# 1. Clone
git clone https://github.com/yourusername/rca-gpt.git
cd rca-gpt

# 2. Install
pip install -r requirements.txt
pip install -e .

# 3. Verify
python -m rca_gpt.cli --version
```

## Generate Demo Data
```bash
# Generate 100 incidents
python scripts/generate_test_incidents.py --count 100

# Generate cascading patterns
python scripts/generate_cascade_patterns.py

# Train model
python -m rca_gpt.cli train
```

## Try It Out
```bash
# View incidents
python -m rca_gpt.cli history

# Show statistics
python -m rca_gpt.cli stats

# Find similar incidents
python -m rca_gpt.cli similar "timeout"

# Discover patterns
python -m rca_gpt.cli patterns

# Launch dashboard
streamlit run dashboard.py
```

## Next Steps

1. Add your own labeled data to `data/training/training_data.csv`
2. Retrain: `python -m rca_gpt.cli train`
3. Start monitoring: `python -m rca_gpt.cli monitor`
4. Integrate with your log pipeline

See full documentation in `docs/` folder.