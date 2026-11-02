# Contributing to RCA-GPT

Thanks for your interest! Here's how to contribute:

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/rca-gpt.git`
3. Create a branch: `git checkout -b feature/my-feature`
4. Make changes
5. Test: `python -m unittest discover tests/`
6. Commit: `git commit -m "Add feature"`
7. Push: `git push origin feature/my-feature`
8. Create Pull Request

## Code Style

- Use Black for formatting: `black rca_gpt/`
- Follow PEP 8
- Add docstrings to new functions
- Write tests for new features

## Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Be descriptive
- Reference issues: "Fix #123: Description"

## Questions?

Open an issue or email the maintainer.
```

**File: `.gitignore`** (update)
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Data
*.db
*.log
*.csv
data/raw/*
data/training/*
!data/training/.gitkeep
logs/*
!logs/.gitkeep
models/*.pkl

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Test
.coverage
htmlcov/