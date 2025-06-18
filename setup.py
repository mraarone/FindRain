# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="financial-data-platform",
    version="1.0.0",
    author="Financial Platform Team",
    author_email="team@financial-platform.com",
    description="Production-ready financial data platform with AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/financial-data-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        line.strip() 
        for line in open("requirements.txt").readlines() 
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "financial-api=api.main:main",
            "financial-websocket=api.data.streaming:main",
            "financial-agent=agents.orchestrator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.sql"],
    },
)
