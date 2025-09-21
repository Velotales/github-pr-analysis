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

def run_git_command(cmd, repo_path='.'):
    """Run a git command in the specified repository"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True,
            cwd=repo_path
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def get_merge_commits(repo_path='.', branch='main'):
    """Get all merge commits in the repository"""
    print(f"Analyzing merge commits on {branch} branch...")
    
    # Get merge commits (commits with more than one parent)
    cmd = f'git log --merges --pretty=format:"%H|%P|%s|%ai|%an" {branch}'
    output = run_git_command(cmd, repo_path)
    
    if not output:
        return []
    
    merge_commits = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 5:
                hash_val, parents, subject, date, author = parts[:5]
                merge_commits.append({
                    'hash': hash_val,
                    'parents': parents.split(),
                    'subject': subject,
                    'date': date,
                    'author': author,
                    'is_pr_merge': 'pull request' in subject.lower() or 'merge pull request' in subject.lower()
                })
    
    return merge_commits

def get_all_commits(repo_path='.', branch='main'):
    """Get all commits on the main branch"""
    print(f"Getting all commits on {branch} branch...")
    
    cmd = f'git rev-list --count {branch}'
    total_commits = run_git_command(cmd, repo_path)
    
    print(f"Total commits on {branch}: {total_commits}")
    
    # Get detailed commit info
    cmd = f'git log --pretty=format:"%H|%s|%ai|%an|%P" {branch}'
    output = run_git_command(cmd, repo_path)
    
    if not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 4:
                hash_val, subject, date, author = parts[:4]
                parents = parts[4] if len(parts) > 4 else ""
                
                commits.append({
                    'hash': hash_val,
                    'subject': subject,
                    'date': date,
                    'author': author,
                    'parents': parents.split() if parents else [],
                    'is_merge': len(parents.split()) > 1 if parents else False
                })
    
    return commits

def analyze_pr_vs_direct_commits(repo_path='.', branch='main'):
    """Analyze the ratio of PR commits vs direct commits"""
    print("\n" + "="*60)
    print("PR vs DIRECT COMMIT ANALYSIS")
    print("="*60)
    
    # Get all commits
    all_commits = get_all_commits(repo_path, branch)
    merge_commits = get_merge_commits(repo_path, branch)
    
    if not all_commits:
        print("No commits found!")
        return
    
    total_commits = len(all_commits)
    merge_count = len(merge_commits)
    
    # Identify PR merge commits
    pr_merges = [c for c in merge_commits if c['is_pr_merge']]
    pr_merge_count = len(pr_merges)
    
    # Estimate commits that came through PRs
    # This is tricky because we need to identify which commits were part of merged PRs
    pr_commits = 0
    
    # For a more accurate analysis, we'd need to:
    # 1. For each PR merge, get the commits that were merged
    # 2. This requires analyzing the commit graph more deeply
    
    # Simple estimation: assume each PR merge represents multiple commits
    # We can get a rough estimate by looking at non-merge commits vs merge commits
    non_merge_commits = total_commits - merge_count
    
    print(f"Total commits: {total_commits}")
    print(f"Merge commits: {merge_count}")
    print(f"PR merge commits: {pr_merge_count}")
    print(f"Non-merge commits: {non_merge_commits}")
    
    # Try to get more accurate PR commit count
    if pr_merges:
        print(f"\nEstimating commits per PR...")
        
        # Sample a few PR merges to estimate average commits per PR
        sample_pr_commits = []
        for pr_merge in pr_merges[:10]:  # Sample first 10 PR merges
            if len(pr_merge['parents']) >= 2:
                # Count commits between the merge base and the PR head
                merge_base = pr_merge['parents'][0]  # Main branch parent
                pr_head = pr_merge['parents'][1]     # PR branch parent
                
                cmd = f'git rev-list --count {merge_base}..{pr_head}'
                pr_commit_count = run_git_command(cmd, repo_path)
                
                if pr_commit_count and pr_commit_count.isdigit():
                    sample_pr_commits.append(int(pr_commit_count))
        
        if sample_pr_commits:
            avg_commits_per_pr = statistics.mean(sample_pr_commits)
            estimated_pr_commits = int(pr_merge_count * avg_commits_per_pr)
            estimated_direct_commits = non_merge_commits - estimated_pr_commits
            
            print(f"Average commits per PR (sample): {avg_commits_per_pr:.1f}")
            print(f"Estimated commits through PRs: {estimated_pr_commits}")
            print(f"Estimated direct commits: {max(0, estimated_direct_commits)}")
            
            if estimated_pr_commits > 0:
                pr_percentage = (estimated_pr_commits / total_commits) * 100
                direct_percentage = (max(0, estimated_direct_commits) / total_commits) * 100
                
                print(f"\nCommit Distribution:")
                print(f"  Commits through PRs: {pr_percentage:.1f}%")
                print(f"  Direct commits: {direct_percentage:.1f}%")
                print(f"  Merge commits: {(merge_count / total_commits) * 100:.1f}%")
    
    return {
        'total_commits': total_commits,
        'merge_commits': merge_count,
        'pr_merges': pr_merge_count,
        'estimated_pr_commits': estimated_pr_commits if 'estimated_pr_commits' in locals() else 0,
        'estimated_direct_commits': estimated_direct_commits if 'estimated_direct_commits' in locals() else non_merge_commits
    }

def compute_pr_vs_direct_commit_ratio(repo_path='.', branch='main'):
    """
    Robustly analyzes all commits on the branch, distinguishing those merged via PRs (using merge commits)
    from direct commits. Prints and returns the counts and ratio.
    """
    print("\n" + "="*60)
    print("ROBUST PR VS DIRECT COMMIT RATIO ANALYSIS")
    print("="*60)

    # Get all commits on the branch
    all_commits = run_git_command(f'git rev-list {branch}', repo_path)
    if not all_commits:
        print("No commits found on branch for analysis.")
        return None
    all_commits = all_commits.splitlines()
    all_commits_set = set(all_commits)
    print(f"Total commits on {branch}: {len(all_commits_set)}")

    # Get all merge commits (typically PR merges)
    merge_commits = run_git_command(f'git log --merges --pretty=format:"%H" {branch}', repo_path)
    if not merge_commits:
        print("No merge commits found.")
        pr_commits_on_main = set()
    else:
        merge_commits = merge_commits.splitlines()
        print(f"Total merge commits: {len(merge_commits)}")
        pr_commits_set = set()
        for merge_sha in merge_commits:
            parents_line = run_git_command(f'git rev-list --parents -n 1 {merge_sha}', repo_path)
            if not parents_line:
                continue
            parents = parents_line.split()
            if len(parents) >= 3:
                # merge_sha parent1 parent2
                parent1, parent2 = parents[1], parents[2]
                # Commits in PR: those in parent2 not in parent1
                pr_commits = run_git_command(f'git rev-list {parent2} ^{parent1}', repo_path)
                if pr_commits:
                    pr_commits_set.update(pr_commits.splitlines())
        # Only count PR commits that are present on the main branch
        pr_commits_on_main = pr_commits_set & all_commits_set

    direct_commits = all_commits_set - pr_commits_on_main

    print(f"Commits merged via PRs: {len(pr_commits_on_main)}")
    print(f"Direct commits: {len(direct_commits)}")
    if len(all_commits_set) > 0:
        print(f"Ratio (PR:Direct): {len(pr_commits_on_main)}/{len(direct_commits)} "
              f"({len(pr_commits_on_main)/len(all_commits_set)*100:.1f}% PR, "
              f"{len(direct_commits)/len(all_commits_set)*100:.1f}% direct)")
    else:
        print("No commits to calculate ratio.")

    return {
        'total_commits': len(all_commits_set),
        'pr_commits': len(pr_commits_on_main),
        'direct_commits': len(direct_commits),
        'pr_ratio': len(pr_commits_on_main)/len(all_commits_set) if all_commits_set else 0,
        'direct_ratio': len(direct_commits)/len(all_commits_set) if all_commits_set else 0,
    }

def analyze_commit_timeline(repo_path='.', branch='main'):
    """Analyze commit patterns over time"""
    print("\n" + "="*60)
    print("COMMIT TIMELINE ANALYSIS")
    print("="*60)
    
    # Get commits with dates
    cmd = f'git log --pretty=format:"%ai|%s" {branch} --since="1 year ago"'
    output = run_git_command(cmd, repo_path)
    
    if not output:
        print("No commits found in the last year")
        return
    
    commits_by_month = defaultdict(list)
    merge_commits_by_month = defaultdict(int)
    
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|', 1)
            if len(parts) >= 2:
                date_str, subject = parts
                try:
                    commit_date = datetime.fromisoformat(date_str.replace(' +', '+'))
                    month_key = commit_date.strftime('%Y-%m')
                    commits_by_month[month_key].append(subject)
                    
                    if any(keyword in subject.lower() for keyword in ['merge pull request', 'merge branch']):
                        merge_commits_by_month[month_key] += 1
                        
                except ValueError:
                    continue
    
    print(f"Commits by month (last 12 months):")
    for month in sorted(commits_by_month.keys()):
        total_commits = len(commits_by_month[month])
        merges = merge_commits_by_month[month]
        regular_commits = total_commits - merges
        
        print(f"  {month}: {total_commits} commits ({regular_commits} regular, {merges} merges)")

def get_repository_stats(repo_path='.'):
    """Get basic repository statistics"""
    print("="*60)
    print("REPOSITORY INFORMATION")
    print("="*60)
    
    # Get repository name and remote
    repo_name = os.path.basename(os.path.abspath(repo_path))
    
    remote_url = run_git_command('git config --get remote.origin.url', repo_path)
    
    # Get branch info
    current_branch = run_git_command('git branch --show-current', repo_path)
    all_branches = run_git_command('git branch -r', repo_path)
    
    # Get contributor count
    contributors = run_git_command('git shortlog -sn --all', repo_path)
    contributor_count = len(contributors.split('\n')) if contributors else 0
    
    print(f"Repository: {repo_name}")
    print(f"Remote URL: {remote_url}")
    print(f"Current branch: {current_branch}")
    print(f"Contributors: {contributor_count}")
    
    if all_branches:
        branch_count = len([b for b in all_branches.split('\n') if b.strip()])
        print(f"Remote branches: {branch_count}")
    
    return repo_name, current_branch

def main():
    parser = argparse.ArgumentParser(description='Analyze git commit patterns')
    parser.add_argument('--repo-path', default='.', help='Path to git repository (default: current directory)')
    parser.add_argument('--branch', default='main', help='Branch to analyze (default: main)')
    
    args = parser.parse_args()
    
    # Check if we're in a git repository
    if not os.path.exists(os.path.join(args.repo_path, '.git')):
        print(f"Error: {args.repo_path} is not a git repository")
        print("Please run this script from within a git repository or specify --repo-path")
        sys.exit(1)
    
    # Check if the branch exists
    branches = run_git_command(f'git branch -a', args.repo_path)
    if branches and args.branch not in branches:
        # Try 'master' if 'main' doesn't exist
        if args.branch == 'main' and 'master' in branches:
            args.branch = 'master'
            print(f"Branch 'main' not found, using 'master' instead")
        else:
            print(f"Warning: Branch '{args.branch}' not found")
    
    # Get repository info
    repo_name, current_branch = get_repository_stats(args.repo_path)
    
    # Analyze commits
    commit_stats = analyze_pr_vs_direct_commits(args.repo_path, args.branch)
    
    # === Robust PR vs Direct commit ratio analysis ===
    pr_direct_stats = compute_pr_vs_direct_commit_ratio(args.repo_path, args.branch)
    
    # Timeline analysis
    analyze_commit_timeline(args.repo_path, args.branch)
    
    # Summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    
    if commit_stats:
        total = commit_stats['total_commits']
        pr_commits = commit_stats['estimated_pr_commits']
        direct_commits = commit_stats['estimated_direct_commits']
        
        print(f"Repository: {repo_name}")
        print(f"Branch analyzed: {args.branch}")
        print(f"Total commits: {total}")
        
        if pr_commits > 0:
            print(f"Estimated PR workflow usage: {(pr_commits / total) * 100:.1f}%")
            print(f"Estimated direct commits: {(direct_commits / total) * 100:.1f}%")
        
        print(f"PR merge commits: {commit_stats['pr_merges']}")
    if pr_direct_stats:
        print("\n== Robust commit ratio analysis ==")
        print(f"PR commits: {pr_direct_stats['pr_commits']} ({pr_direct_stats['pr_ratio']*100:.1f}%)")
        print(f"Direct commits: {pr_direct_stats['direct_commits']} ({pr_direct_stats['direct_ratio']*100:.1f}%)")
        print(f"Total commits (robust): {pr_direct_stats['total_commits']}")

if __name__ == '__main__':
    main()
