#!/bin/bash

# GitHub Repository Analysis Tool
# This script helps analyze commit patterns in GitHub repositories

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <owner/repo> [options]"
    echo ""
    echo "Options:"
    echo "  --clone-only       Only clone the repository, don't analyze"
    echo "  --github-only      Only analyze using GitHub API (requires gh auth)"
    echo "  --local-only       Only analyze local git history"
    echo "  --branch BRANCH    Specify branch to analyze (default: main)"
    echo "  --limit N          Limit number of PRs to analyze via GitHub API (default: 100)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 microsoft/vscode"
    echo "  $0 facebook/react --branch master --limit 50"
    echo "  $0 torvalds/linux --local-only"
    exit 1
}

print_header() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE} GitHub Repository Commit Pattern Analysis${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        echo -e "${YELLOW}Cleaning up temporary directory: $TEMP_DIR${NC}"
        rm -rf "$TEMP_DIR"
    fi
}

# Parse arguments
REPO=""
BRANCH="main"
LIMIT=100
CLONE_ONLY=false
GITHUB_ONLY=false
LOCAL_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clone-only)
            CLONE_ONLY=true
            shift
            ;;
        --github-only)
            GITHUB_ONLY=true
            shift
            ;;
        --local-only)
            LOCAL_ONLY=true
            shift
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
        *)
            if [[ -z "$REPO" ]]; then
                REPO="$1"
            else
                echo -e "${RED}Multiple repositories specified${NC}"
                usage
            fi
            shift
            ;;
    esac
done

if [[ -z "$REPO" ]]; then
    echo -e "${RED}Error: Repository not specified${NC}"
    usage
fi

# Validate repository format
if [[ ! "$REPO" =~ ^[^/]+/[^/]+$ ]]; then
    echo -e "${RED}Error: Repository must be in format 'owner/repo'${NC}"
    exit 1
fi

print_header

# Set up cleanup trap
trap cleanup EXIT

# Check if we're analyzing a local repository or need to clone
if [[ -d "$REPO" ]]; then
    echo -e "${GREEN}Found local repository: $REPO${NC}"
    REPO_PATH="$REPO"
elif [[ -d ".git" ]]; then
    echo -e "${GREEN}Using current directory as repository${NC}"
    REPO_PATH="."
    # Try to determine repository name from remote
    REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
    if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+/[^/]+)(\.git)?$ ]]; then
        REPO="${BASH_REMATCH[1]}"
        echo -e "${BLUE}Detected repository: $REPO${NC}"
    fi
else
    echo -e "${YELLOW}Cloning repository: $REPO${NC}"
    TEMP_DIR=$(mktemp -d)
    REPO_PATH="$TEMP_DIR/$(basename $REPO)"
    
    # Clone with limited depth for faster analysis
    if ! git clone "https://github.com/$REPO.git" "$REPO_PATH" --depth 200; then
        echo -e "${RED}Failed to clone repository${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Repository cloned to: $REPO_PATH${NC}"
fi

if [[ "$CLONE_ONLY" == true ]]; then
    echo -e "${GREEN}Repository cloned. Skipping analysis.${NC}"
    echo -e "${BLUE}To analyze manually, run:${NC}"
    echo "  cd $REPO_PATH"
    echo "  python3 ./git_commit_analysis.py --branch $BRANCH"
    exit 0
fi

# Run GitHub API analysis if requested and authenticated
if [[ "$LOCAL_ONLY" == false ]]; then
    echo -e "${YELLOW}Checking GitHub CLI authentication...${NC}"
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}GitHub CLI authenticated. Running GitHub API analysis...${NC}"
        echo ""
        python3 ./github_pr_metrics.py "$REPO" --limit "$LIMIT"
    else
        echo -e "${YELLOW}GitHub CLI not authenticated. Skipping GitHub API analysis.${NC}"
        echo -e "${BLUE}To enable GitHub API analysis, run: gh auth login${NC}"
        
        if [[ "$GITHUB_ONLY" == true ]]; then
            echo -e "${RED}Cannot run GitHub-only analysis without authentication${NC}"
            exit 1
        fi
    fi
fi

# Run local git analysis if requested
if [[ "$GITHUB_ONLY" == false ]]; then
    echo ""
    echo -e "${GREEN}Running local git history analysis...${NC}"
    echo ""
    python3 ./git_commit_analysis.py --repo-path "$REPO_PATH" --branch "$BRANCH"
fi

echo ""
echo -e "${GREEN}Analysis complete!${NC}"