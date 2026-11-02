from setuptools import setup, find_packages

setup(
    name="obs-stack",
    version="3.0.0-alpha",
    description="Instant Observability for Any App",
    author="Naga Sowmya Ganti",
    packages=find_packages(),
    install_requires=[
        "docker>=7.0.0",
        "pyyaml>=6.0.1",
        "jinja2>=3.1.2",
        "click>=8.1.7",
        "rich>=13.7.0",
        "requests>=2.31.0",
    ],
    entry_points={
        'console_scripts': [
            'obs-stack=cli.main:cli',
        ],
    },
    python_requires='>=3.10',
)
