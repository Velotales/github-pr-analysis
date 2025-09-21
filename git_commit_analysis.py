#!/usr/bin/env python3
"""
Advanced Git Commit Pattern Analysis

This script provides detailed analysis of commit patterns in a git repository:
- Identifies commits that went through PRs vs direct commits to main/master
- Analyzes commit frequency patterns over time
- Provides detailed statistics about development workflow

Usage:
    # Clone a repository first, then run from within it:
    git clone https://github.com/owner/repo
    cd repo
    python3 /path/to/git_commit_analysis.py
    
    # Or specify a repository path:
    python3 git_commit_analysis.py --repo-path /path/to/repo --branch main

Requirements:
    - Git repository (local)
    - Python 3.6+
"""

import subprocess
import sys
import argparse
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import os

def run_git_command(cmd, repo_path='.'): ... [TRUNCATED FOR BREVITY] ...
if __name__ == '__main__':
    main()