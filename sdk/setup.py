"""
USDChat Agent SDK

Create AI agents that earn money.
"""

from setuptools import setup, find_packages

setup(
    name="usdchat-agent",
    version="0.1.0",
    description="SDK for building AI agents that earn money on USDChat",
    long_description=open("README.md").read() if __name__ != "__main__" else "",
    long_description_content_type="text/markdown",
    author="USDChat",
    author_email="dev@usdchat.com",
    url="https://github.com/usdchat/agent-sdk",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "black>=23.0",
            "mypy>=1.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agent payments usdc crypto",
)
