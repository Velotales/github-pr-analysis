#!/usr/bin/env python3
"""
GitHub Organization Repository Analysis Tool

This script analyzes all repositories in a GitHub organization to understand
commit patterns across the entire organization:
- Discovers all repositories the user has access to
- Runs PR metrics analysis on each repository
- Generates organization-wide summary reports
- Exports results to CSV for further analysis

Usage:
    python3 analyze_org_repos.py <organization> [options]

Examples:
    python3 analyze_org_repos.py mycompany
    python3 analyze_org_repos.py mycompany --private-only --limit 50
    python3 analyze_org_repos.py mycompany --export-csv results.csv

Requirements:
    - GitHub CLI (gh) must be installed and authenticated
    - Python 3.6+
"""

import json
import subprocess
import sys
import argparse
import csv
import os
from datetime import datetime
from collections import defaultdict, Counter
import statistics
import time

def run_command(cmd, timeout=300):
    """Run a shell command with timeout and return the output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def get_organization_repos(org, include_private=True, include_public=True):
    """Get all repositories in an organization that the user has access to"""
    print(f"Discovering repositories in organization: {org}")
    
    # Build the command
    cmd_parts = ['gh', 'repo', 'list', org, '--json', 'name,private,language,updatedAt,pushedAt,stargazerCount']
    
    if include_private and not include_public:
        cmd_parts.extend(['--visibility', 'private'])
    elif include_public and not include_private:
        cmd_parts.extend(['--visibility', 'public'])
    # If both are True, we get all repositories (default)
    
    cmd_parts.append('--limit')
    cmd_parts.append('1000')  # GitHub CLI default limit
    
    cmd = ' '.join(cmd_parts)
    output = run_command(cmd)
    
    if not output:
        return []
    
    try:
        repos = json.loads(output)
        print(f"Found {len(repos)} repositories")
        
        # Filter by activity if needed (optional)
        active_repos = []
        for repo in repos:
            # Skip repos that haven't been updated in over a year (optional filter)
            if repo.get('updatedAt'):
                try:
                    updated = datetime.fromisoformat(repo['updatedAt'].replace('Z', '+00:00'))
                    days_since_update = (datetime.now().astimezone() - updated).days
                    if days_since_update < 365:  # Only include repos updated in last year
                        active_repos.append(repo)
                except ValueError:
                    active_repos.append(repo)  # Include if we can't parse date
            else:
                active_repos.append(repo)
        
        print(f"Active repositories (updated in last year): {len(active_repos)}")
        return active_repos
    except json.JSONDecodeError:
        print("Error parsing repository data")
        return []

def analyze_single_repo(org, repo_name, pr_limit=100):
    """Analyze a single repository and return metrics"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {org}/{repo_name}")
    print(f"{'='*60}")
    
    full_repo_name = f"{org}/{repo_name}"
    
    # Get basic repo info
    repo_cmd = f'gh repo view {full_repo_name} --json name,description,language,stargazerCount,forkCount,defaultBranch,pushedAt'
    repo_info_raw = run_command(repo_cmd)
    
    repo_info = {}
    if repo_info_raw:
        try:
            repo_info = json.loads(repo_info_raw)
        except json.JSONDecodeError:
            pass
    
    # Get pull requests
    pr_cmd = f'gh pr list --repo {full_repo_name} --state all --limit {pr_limit} --json number,title,commits,mergedAt,createdAt,author'
    pr_output = run_command(pr_cmd, timeout=120)
    
    metrics = {
        'repo_name': repo_name,
        'full_name': full_repo_name,
        'language': repo_info.get('language', 'Unknown'),
        'stars': repo_info.get('stargazerCount', 0),
        'forks': repo_info.get('forkCount', 0),
        'default_branch': repo_info.get('defaultBranch', 'main'),
        'last_push': repo_info.get('pushedAt', 'Unknown'),
        'total_prs': 0,
        'merged_prs': 0,
        'merge_rate': 0.0,
        'avg_commits_per_pr': 0.0,
        'median_commits_per_pr': 0.0,
        'total_pr_commits': 0,
        'single_commit_prs': 0,
        'small_prs': 0,
        'medium_prs': 0,
        'large_prs': 0,
        'analysis_date': datetime.now().isoformat()
    }
    
    if not pr_output:
        print(f"No PR data available for {repo_name}")
        return metrics
    
    try:
        prs = json.loads(pr_output)
        metrics['total_prs'] = len(prs)
        
        if not prs:
            print(f"No pull requests found in {repo_name}")
            return metrics
        
        # Filter merged PRs
        merged_prs = [pr for pr in prs if pr.get('mergedAt')]
        metrics['merged_prs'] = len(merged_prs)
        
        if metrics['total_prs'] > 0:
            metrics['merge_rate'] = (metrics['merged_prs'] / metrics['total_prs']) * 100
        
        # Analyze commit counts (sample first 20 PRs to avoid rate limits)
        commit_counts = []
        sample_size = min(20, len(merged_prs))
        
        print(f"Analyzing commits in {sample_size} merged PRs...")
        
        for i, pr in enumerate(merged_prs[:sample_size]):
            pr_number = pr['number']
            
            # Get PR commit details
            pr_detail_cmd = f'gh pr view {pr_number} --repo {full_repo_name} --json commits'
            pr_detail = run_command(pr_detail_cmd, timeout=30)
            
            if pr_detail:
                try:
                    pr_data = json.loads(pr_detail)
                    commits = pr_data.get('commits', [])
                    commit_count = len(commits)
                    commit_counts.append(commit_count)
                    
                    # Categorize PR size
                    if commit_count == 1:
                        metrics['single_commit_prs'] += 1
                    elif commit_count <= 3:
                        metrics['small_prs'] += 1
                    elif commit_count <= 10:
                        metrics['medium_prs'] += 1
                    else:
                        metrics['large_prs'] += 1
                        
                except json.JSONDecodeError:
                    continue
            
            # Add delay to avoid rate limiting
            time.sleep(0.1)
        
        # Calculate statistics
        if commit_counts:
            metrics['avg_commits_per_pr'] = statistics.mean(commit_counts)
            metrics['median_commits_per_pr'] = statistics.median(commit_counts)
            metrics['total_pr_commits'] = sum(commit_counts)
            
            # Scale up the totals based on sample size
            if sample_size < len(merged_prs):
                scale_factor = len(merged_prs) / sample_size
                metrics['total_pr_commits'] = int(metrics['total_pr_commits'] * scale_factor)
                
                for key in ['single_commit_prs', 'small_prs', 'medium_prs', 'large_prs']:
                    metrics[key] = int(metrics[key] * scale_factor)
        
        # Print summary
        print(f"Results for {repo_name}:")
        print(f"  Total PRs: {metrics['total_prs']}")
        print(f"  Merged PRs: {metrics['merged_prs']} ({metrics['merge_rate']:.1f}%)")
        print(f"  Avg commits per PR: {metrics['avg_commits_per_pr']:.1f}")
        print(f"  Primary language: {metrics['language']}")
        
    except json.JSONDecodeError:
        print(f"Error parsing PR data for {repo_name}")
    
    return metrics

def generate_org_summary(all_metrics, org_name):
    """Generate organization-wide summary statistics"""
    print(f"\n{'='*80}")
    print(f"ORGANIZATION SUMMARY: {org_name}")
    print(f"{'='*80}")
    
    if not all_metrics:
        print("No data to summarize")
        return
    
    # Overall statistics
    total_repos = len(all_metrics)
    repos_with_prs = len([m for m in all_metrics if m['total_prs'] > 0])
    
    total_prs = sum(m['total_prs'] for m in all_metrics)
    total_merged = sum(m['merged_prs'] for m in all_metrics)
    
    print(f"Repositories analyzed: {total_repos}")
    print(f"Repositories with PRs: {repos_with_prs}")
    print(f"Total pull requests: {total_prs}")
    print(f"Total merged PRs: {total_merged}")
    
    if total_prs > 0:
        org_merge_rate = (total_merged / total_prs) * 100
        print(f"Organization merge rate: {org_merge_rate:.1f}%")
    
    # Language distribution
    languages = Counter(m['language'] for m in all_metrics if m['language'] != 'Unknown')
    print(f"\nTop languages:")
    for lang, count in languages.most_common(5):
        print(f"  {lang}: {count} repositories")
    
    # PR size distribution
    total_single = sum(m['single_commit_prs'] for m in all_metrics)
    total_small = sum(m['small_prs'] for m in all_metrics)
    total_medium = sum(m['medium_prs'] for m in all_metrics)
    total_large = sum(m['large_prs'] for m in all_metrics)
    total_sized = total_single + total_small + total_medium + total_large
    
    if total_sized > 0:
        print(f"\nPR Size Distribution (organization-wide):")
        print(f"  Single commit: {total_single} ({(total_single/total_sized)*100:.1f}%)")
        print(f"  Small (2-3 commits): {total_small} ({(total_small/total_sized)*100:.1f}%)")
        print(f"  Medium (4-10 commits): {total_medium} ({(total_medium/total_sized)*100:.1f}%)")
        print(f"  Large (10+ commits): {total_large} ({(total_large/total_sized)*100:.1f}%)")
    
    # Average metrics across repositories
    repos_with_data = [m for m in all_metrics if m['avg_commits_per_pr'] > 0]
    if repos_with_data:
        avg_commits_org = statistics.mean(m['avg_commits_per_pr'] for m in repos_with_data)
        print(f"\nAverage commits per PR (across all repos): {avg_commits_org:.1f}")
    
    # Most active repositories
    print(f"\nMost active repositories (by PR count):")
    sorted_by_prs = sorted(all_metrics, key=lambda x: x['total_prs'], reverse=True)
    for repo in sorted_by_prs[:10]:
        if repo['total_prs'] > 0:
            print(f"  {repo['repo_name']}: {repo['total_prs']} PRs, {repo['merged_prs']} merged")

def export_to_csv(all_metrics, filename):
    """Export results to CSV file"""
    print(f"\nExporting results to {filename}...")
    
    fieldnames = [
        'repo_name', 'full_name', 'language', 'stars', 'forks', 'default_branch',
        'total_prs', 'merged_prs', 'merge_rate', 'avg_commits_per_pr', 'median_commits_per_pr',
        'total_pr_commits', 'single_commit_prs', 'small_prs', 'medium_prs', 'large_prs',
        'last_push', 'analysis_date'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for metrics in all_metrics:
            writer.writerow(metrics)
    
    print(f"Results exported to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Analyze all repositories in a GitHub organization')
    parser.add_argument('organization', help='GitHub organization name')
    parser.add_argument('--private-only', action='store_true', help='Only analyze private repositories')
    parser.add_argument('--public-only', action='store_true', help='Only analyze public repositories')
    parser.add_argument('--limit', type=int, default=100, help='Limit PRs per repository (default: 100)')
    parser.add_argument('--repo-limit', type=int, default=None, help='Limit number of repositories to analyze')
    parser.add_argument('--export-csv', help='Export results to CSV file')
    parser.add_argument('--skip-analysis', action='store_true', help='Only list repositories, skip analysis')
    
    args = parser.parse_args()
    
    # Check if gh is authenticated
    auth_check = run_command('gh auth status')
    if not auth_check or 'Logged in' not in auth_check:
        print("Error: GitHub CLI not authenticated")
        print("Please run: gh auth login")
        sys.exit(1)
    
    # Validate organization access
    print(f"Checking access to organization: {args.organization}")
    org_check = run_command(f'gh api orgs/{args.organization}')
    if not org_check:
        print(f"Error: Cannot access organization '{args.organization}'")
        print("Please check that:")
        print("1. The organization name is correct")
        print("2. You have access to the organization")
        print("3. Your GitHub token has the necessary permissions")
        sys.exit(1)
    
    # Determine repository visibility settings
    include_private = not args.public_only
    include_public = not args.private_only
    
    # Get repositories
    repos = get_organization_repos(args.organization, include_private, include_public)
    
    if not repos:
        print("No repositories found or accessible")
        sys.exit(1)
    
    # Apply repository limit if specified
    if args.repo_limit:
        repos = repos[:args.repo_limit]
        print(f"Limited analysis to first {len(repos)} repositories")
    
    if args.skip_analysis:
        print("\nRepositories found:")
        for repo in repos:
            privacy = "private" if repo.get('private', False) else "public"
            print(f"  {repo['name']} ({privacy}) - {repo.get('language', 'Unknown')}")
        return
    
    # Analyze each repository
    all_metrics = []
    total_repos = len(repos)
    
    print(f"\nStarting analysis of {total_repos} repositories...")
    
    for i, repo in enumerate(repos, 1):
        print(f"\nProgress: {i}/{total_repos}")
        try:
            metrics = analyze_single_repo(args.organization, repo['name'], args.limit)
            all_metrics.append(metrics)
        except KeyboardInterrupt:
            print(f"\nAnalysis interrupted by user after {i-1} repositories")
            break
        except Exception as e:
            print(f"Error analyzing {repo['name']}: {e}")
            continue
    
    # Generate summary report
    generate_org_summary(all_metrics, args.organization)
    
    # Export to CSV if requested
    if args.export_csv:
        export_to_csv(all_metrics, args.export_csv)
    
    print(f"\nAnalysis complete! Analyzed {len(all_metrics)} repositories.")

if __name__ == '__main__':
    main()