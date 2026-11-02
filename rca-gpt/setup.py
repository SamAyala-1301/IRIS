from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rca-gpt",
    version="1.1.0",
    author="Sai Sampath Ayalasomayajula",
    description="AI-powered root cause analysis for support engineers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/rca-gpt",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0",
        "sqlalchemy>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "rca-gpt=rca_gpt.cli:main",
        ],
    },
)