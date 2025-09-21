#!/bin/bash

# Initialize Git Repository for GitHub PR Analysis Tools
# This script helps set up the project as a Git repository ready for GitHub

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}GitHub PR Analysis Tools - Git Repository Setup${NC}"
echo "=================================================="
echo ""

# Check if already a git repository
if [[ -d ".git" ]]; then
    echo -e "${YELLOW}This directory is already a Git repository.${NC}"
    echo ""
    git status
    exit 0
fi

echo -e "${GREEN}Initializing Git repository...${NC}"
git init

echo -e "${GREEN}Adding all files...${NC}"
git add .

echo -e "${GREEN}Creating initial commit...${NC}"
git commit -m "Initial commit: GitHub PR Analysis Tools

- Organization-wide repository analysis
- Individual repository PR metrics
- CSV export functionality  
- Interactive setup and authentication helpers
- Comprehensive documentation

Tools included:
- analyze_repos.py: Main repository analysis (orgs & users)
- setup_analysis.sh: Interactive setup helper
- github_pr_metrics.py: Single repo GitHub API analysis
- git_commit_analysis.py: Local git history analysis
- analyze_repo.sh: Single repo wrapper script

echo ""
echo -e "${GREEN}Git repository initialized successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create a repository on GitHub"
echo "2. Add remote origin:"
echo "   ${BLUE}git remote add origin https://github.com/yourusername/github-pr-analysis.git${NC}"
echo "3. Push to GitHub:"
echo "   ${BLUE}git branch -M main${NC}"
echo "   ${BLUE}git push -u origin main${NC}"
echo ""
echo -e "${BLUE}Repository is ready for GitHub!${NC}"