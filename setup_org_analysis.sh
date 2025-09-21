#!/bin/bash

# Organization Analysis Setup Script
# This script helps set up and run organization-wide PR analysis

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "================================================================="
    echo " GitHub Organization PR Analysis - Setup & Usage Guide"
    echo "================================================================="
    echo -e "${NC}"
}

check_authentication() {
    echo -e "${YELLOW}Checking GitHub CLI authentication...${NC}"
    
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}✓ GitHub CLI is authenticated${NC}"
        
        # Show current user info
        USER_INFO=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
        echo -e "${BLUE}Authenticated as: ${USER_INFO}${NC}"
        return 0
    else
        echo -e "${RED}✗ GitHub CLI not authenticated${NC}"
        return 1
    fi
}

setup_authentication() {
    echo -e "${YELLOW}Setting up GitHub authentication...${NC}"
    echo ""
    echo "You'll need to authenticate with GitHub to access private repositories."
    echo "This will open a web browser for authentication."
    echo ""
    read -p "Continue with authentication? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh auth login --scopes "repo,read:org"
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ Authentication successful!${NC}"
        else
            echo -e "${RED}✗ Authentication failed${NC}"
            exit 1
        fi
    else
        echo "Authentication cancelled. You can run 'gh auth login' manually later."
        exit 1
    fi
}

show_usage() {
    echo -e "${BLUE}Usage Examples:${NC}"
    echo ""
    echo "1. Analyze all repositories in your organization:"
    echo "   python3 analyze_org_repos.py mycompany"
    echo ""
    echo "2. Analyze only private repositories:"
    echo "   python3 analyze_org_repos.py mycompany --private-only"
    echo ""
    echo "3. Export results to CSV:"
    echo "   python3 analyze_org_repos.py mycompany --export-csv results.csv"
    echo ""
    echo "4. Quick test (first 5 repos only):"
    echo "   python3 analyze_org_repos.py mycompany --repo-limit 5"
    echo ""
    echo "5. Just list repositories without analyzing:"
    echo "   python3 analyze_org_repos.py mycompany --skip-analysis"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --private-only    Only analyze private repositories"
    echo "  --public-only     Only analyze public repositories"
    echo "  --limit N         Limit PRs per repository (default: 100)"
    echo "  --repo-limit N    Limit number of repositories to analyze"
    echo "  --export-csv FILE Export results to CSV file"
    echo "  --skip-analysis   Only list repositories, don't analyze"
}

test_org_access() {
    if [[ -z "$1" ]]; then
        echo -e "${RED}Please provide an organization name to test${NC}"
        return 1
    fi
    
    local ORG="$1"
    echo -e "${YELLOW}Testing access to organization: ${ORG}${NC}"
    
    if gh api "orgs/${ORG}" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Can access organization '${ORG}'${NC}"
        
        # Count repos
        REPO_COUNT=$(gh repo list "$ORG" --limit 1000 --json name | jq length 2>/dev/null || echo "unknown")
        echo -e "${BLUE}Accessible repositories: ${REPO_COUNT}${NC}"
        
        return 0
    else
        echo -e "${RED}✗ Cannot access organization '${ORG}'${NC}"
        echo "This could be because:"
        echo "  - Organization name is incorrect"
        echo "  - You don't have access to the organization"
        echo "  - Your token doesn't have the necessary permissions"
        return 1
    fi
}

main() {
    print_header
    
    # Check if organization is provided
    if [[ $# -eq 0 ]]; then
        echo "This script helps you set up and run PR analysis across all repositories"
        echo "in a GitHub organization."
        echo ""
        
        if ! check_authentication; then
            echo ""
            setup_authentication
        fi
        
        echo ""
        echo -e "${YELLOW}Please provide an organization name to get started:${NC}"
        read -p "Organization name: " ORG_NAME
        
        if [[ -n "$ORG_NAME" ]]; then
            echo ""
            test_org_access "$ORG_NAME"
            echo ""
            show_usage
        fi
        
    elif [[ "$1" == "--help" || "$1" == "-h" ]]; then
        show_usage
    
    elif [[ "$1" == "--test" ]]; then
        if ! check_authentication; then
            setup_authentication
        fi
        
        shift
        test_org_access "$1"
        
    elif [[ "$1" == "--setup" ]]; then
        setup_authentication
        
    else
        # Run the analysis
        ORG_NAME="$1"
        shift
        
        if ! check_authentication; then
            echo ""
            setup_authentication
        fi
        
        echo ""
        echo -e "${GREEN}Running analysis for organization: ${ORG_NAME}${NC}"
        echo ""
        
        python3 "./analyze_org_repos.py" "$ORG_NAME" "$@"
    fi
}

# Make the main script executable
chmod +x "./analyze_org_repos.py" 2>/dev/null || true

main "$@"