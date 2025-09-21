#!/usr/bin/env python3
"""
GitHub Pull Request Metrics Analyzer

This script analyzes GitHub repositories to understand commit patterns:
- How many commits happen in pull requests vs directly on main/master
- Average commits per pull request
- Distribution of PR sizes
- Timeline analysis of commit patterns

Usage:
    python3 github_pr_metrics.py owner/repo [--limit N] [--branch main]
    
Requirements:
    - GitHub CLI (gh) must be installed and authenticated
    - Python 3.6+
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime
from collections import defaultdict, Counter
import statistics

def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def get_pull_requests(repo, limit=100):
    """Fetch pull requests from the repository"""
    print(f"Fetching pull requests from {repo}...")
    
    # Remove 'commits' from the fields here
    cmd = f'gh pr list --repo {repo} --state all --limit {limit} --json number,title,mergedAt,createdAt,baseRefName,headRefName,mergeable'
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        prs = json.loads(output)
        print(f"Found {len(prs)} pull requests")
        return prs
    except json.JSONDecodeError:
        print("Error parsing PR data")
        return []

def get_pr_commits(repo, pr_number):
    """Get detailed commit information for a specific PR"""
    cmd = f'gh pr view {pr_number} --repo {repo} --json commits'
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        pr_data = json.loads(output)
        return pr_data.get('commits', [])
    except json.JSONDecodeError:
        return []

def get_branch_commits(repo, branch='main', limit=500):
    """Get commit SHAs from the branch (default: main)"""
    # Correct usage: add '?sha=branch&per_page=100' to the endpoint
    cmd = f'gh api repos/{repo}/commits?sha={branch}&per_page=100 --paginate -q ".[].sha"'
    output = run_command(cmd)
    if not output:
        return []
    return output.splitlines()

def get_direct_commits(repo, branch='main', since_date=None):
    """Get commits that went directly to main/master branch"""
    print(f"Fetching direct commits to {branch} branch...")
    
    # First, try to clone or work with the repo locally
    # For now, we'll use gh api to get commit data
    cmd = f'gh api repos/{repo}/commits --field sha --field commit.message --field commit.author.date'
    if since_date:
        cmd += f' --field since={since_date}'
    
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        commits = json.loads(output)
        return commits
    except json.JSONDecodeError:
        print("Error parsing commit data")
        return []

def analyze_pr_metrics(prs, repo):
    """Analyze pull request commit metrics"""
    print("\n" + "="*60)
    print("PULL REQUEST COMMIT ANALYSIS")
    print("="*60)
    
    if not prs:
        print("No pull requests found")
        return 0, 0, {}
    
    # Basic statistics
    total_prs = len(prs)
    merged_prs = [pr for pr in prs if pr.get('mergedAt')]
    
    print(f"Total Pull Requests: {total_prs}")
    print(f"Merged Pull Requests: {len(merged_prs)}")
    print(f"Merge Rate: {len(merged_prs)/total_prs*100:.1f}%")
    
    # Analyze commit counts per PR
    commit_counts = []
    pr_sizes = Counter()
    
    print(f"\nAnalyzing commits in {len(merged_prs)} merged PRs...")
    
    for i, pr in enumerate(merged_prs[:50]):  # Limit to first 50 for API rate limiting
        pr_number = pr['number']
        commits = get_pr_commits(repo, pr_number)
        
        if commits:
            commit_count = len(commits)
            commit_counts.append(commit_count)
            
            # Categorize PR size
            if commit_count == 1:
                pr_sizes['Single commit'] += 1
            elif commit_count <= 3:
                pr_sizes['Small (2-3 commits)'] += 1
            elif commit_count <= 10:
                pr_sizes['Medium (4-10 commits)'] += 1
            else:
                pr_sizes['Large (10+ commits)'] += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(merged_prs)} PRs...")
    
    # Calculate statistics
    if commit_counts:
        avg_commits = statistics.mean(commit_counts)
        median_commits = statistics.median(commit_counts)
        total_pr_commits = sum(commit_counts)
        
        print(f"\nCOMMIT STATISTICS:")
        print(f"Total commits in PRs: {total_pr_commits}")
        print(f"Average commits per PR: {avg_commits:.1f}")
        print(f"Median commits per PR: {median_commits}")
        print(f"Min commits in a PR: {min(commit_counts)}")
        print(f"Max commits in a PR: {max(commit_counts)}")
        
        print(f"\nPR SIZE DISTRIBUTION:")
        for size, count in pr_sizes.most_common():
            percentage = (count / len(commit_counts)) * 100
            print(f"  {size}: {count} PRs ({percentage:.1f}%)")
        
        return total_pr_commits, avg_commits, pr_sizes
    
    return 0, 0, {}

def get_repository_info(repo):
    """Get basic repository information"""
    cmd = f'gh repo view {repo} --json name,owner,defaultBranchRef,pushedAt'
    output = run_command(cmd)
    
    if output:
        try:
            repo_info = json.loads(output)
            return repo_info
        except json.JSONDecodeError:
            pass
    
    return {}

def main():
    parser = argparse.ArgumentParser(description='Analyze GitHub PR commit metrics')
    parser.add_argument('repo', help='Repository in format owner/repo')
    parser.add_argument('--limit', type=int, default=100, help='Limit number of PRs to analyze')
    parser.add_argument('--branch', default='main', help='Main branch name (default: main)')
    
    args = parser.parse_args()
    
    # Check if gh is authenticated
    auth_check = run_command('gh auth status')
    if not auth_check or 'Logged in' not in auth_check:
        print("Please authenticate with GitHub CLI first:")
        print("Run: gh auth login")
        sys.exit(1)
    
    print(f"Analyzing repository: {args.repo}")
    
    # Get repository info
    repo_info = get_repository_info(args.repo)
    if repo_info:
        default_branch = (repo_info.get('defaultBranchRef') or {}).get('name', args.branch)
        print(f"Default branch: {default_branch}")
        args.branch = default_branch
    
    # Analyze pull requests
    prs = get_pull_requests(args.repo, args.limit)
    total_pr_commits, avg_commits, pr_sizes = analyze_pr_metrics(prs, args.repo)

    # --- Direct commit analysis ---
    print(f"\n" + "="*60)
    print("DIRECT COMMIT ANALYSIS")
    print("="*60)
    print("Counting direct commits to the default branch...")

    # 1. Get all commit SHAs from merged PRs
    merged_pr_shas = set()
    for pr in prs:
        if pr.get('mergedAt'):
            commits = get_pr_commits(args.repo, pr['number'])
            merged_pr_shas.update(c['oid'] for c in commits if 'oid' in c)

    # 2. Get all commit SHAs from the default branch
    branch_shas = get_branch_commits(args.repo, args.branch)

    # 3. Count SHAs on branch that are not in merged PRs
    direct_commits = [sha for sha in branch_shas if sha not in merged_pr_shas]
    print(f"Total commits on branch '{args.branch}': {len(branch_shas)}")
    print(f"Direct commits (not in merged PRs): {len(direct_commits)}")

    # Summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Repository: {args.repo}")
    print(f"Total PR commits analyzed: {total_pr_commits}")
    print(f"Average commits per PR: {avg_commits:.1f}")
    
    if pr_sizes:
        print(f"Most common PR size: {max(pr_sizes.items(), key=lambda x: x[1])[0]}")

if __name__ == '__main__':
    main()