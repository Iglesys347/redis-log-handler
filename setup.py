#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name="redis-logs",
    description="Python log handler to forward logs to Redis database",
    long_description=open("README.md").read().strip(),
    long_description_content_type="text/markdown",
    keywords=["Redis", "logging"],
    license="MIT",
    version="0.0.3",
    packages=find_packages(
        include=[
            "rlh",
            "rlh.handlers",
        ]
    ),
    url="https://github.com/Iglesys347/redis-log-handler",
    project_urls={
        # "Documentation": "TODO:add link to readthedoc",
        "Changes": "https://github.com/Iglesys347/redis-log-handler/releases",
        "Code": "https://github.com/Iglesys347/redis-log-handler",
        "Issue tracker": "https://github.com/Iglesys347/redis-log-handler/issues",
    },
    author="Iglesys347",
    author_email="g.imbert34@gmail.com",
    python_requires=">=3.9",
    install_requires=[
        "redis",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    extras_require={},
)
