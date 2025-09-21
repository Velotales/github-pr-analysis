# GitHub Repository PR Analysis Tools

This collection of tools allows you to analyze pull request metrics across all repositories for a GitHub organization or user, including private repositories you have access to.

> **Note:** All commands should be run from the project directory where these scripts are located.

## 🚀 Quick Start

### 1. Set up authentication and test access:
```bash
./setup_org_analysis.sh
```

### 2. Analyze all repositories for an organization or user:
```bash
python3 analyze_org_repos.py your-company-name    # Organization
python3 analyze_org_repos.py johndoe              # User
```

### 3. Export results to CSV for further analysis:
```bash
python3 analyze_org_repos.py your-account --export-csv results.csv
```

## 📊 What You'll Get

### Account-Wide Metrics:
- **Total repositories analyzed** (organization or user)
- **Overall PR merge rate** across all repositories
- **Language distribution** (which programming languages are most used)
- **PR size patterns** (single commit vs multi-commit PRs)
- **Most active repositories** by PR volume
- **Average commits per PR** across all repositories

### Per-Repository Metrics:
- Total pull requests and merge rate
- Average and median commits per PR
- PR size distribution (single, small, medium, large)
- Repository metadata (language, stars, forks)
- Last push date and activity level

## 🛠 Tools Included

### 1. `analyze_org_repos.py` - Main Analysis Script
The comprehensive tool that discovers and analyzes all repositories in an organization.

**Key Features:**
- Discovers all repositories you have access to (private and public)
- Analyzes PR patterns for each repository
- Generates organization-wide summary reports
- Exports detailed results to CSV
- Handles rate limiting and timeouts gracefully
- Filters out inactive repositories (optional)

### 2. `setup_org_analysis.sh` - Setup Helper
An interactive script that helps with authentication and testing.

**Features:**
- Guides you through GitHub CLI authentication
- Tests organization access before running analysis
- Provides usage examples and options
- Can run the analysis directly with proper setup

### 3. `github_pr_metrics.py` - Single Repository Analysis
For analyzing individual repositories in detail.

### 4. `git_commit_analysis.py` - Local Git History Analysis
For analyzing commit patterns in local repositories.

### 5. `analyze_repo.sh` - Single Repository Wrapper
Easy-to-use script for analyzing individual repositories.

## 📋 Usage Examples

### Basic Analysis
```bash
# Analyze all repositories for an organization
python3 analyze_org_repos.py mycompany

# Analyze all repositories for a user
python3 analyze_org_repos.py johndoe

# Only analyze private repositories
python3 analyze_org_repos.py mycompany --private-only

# Quick test with first 5 repositories only
python3 analyze_org_repos.py johndoe --repo-limit 5
```

### Advanced Options
```bash
# Analyze with custom PR limit per repo and export to CSV
python3 analyze_org_repos.py mycompany --limit 200 --export-csv detailed_results.csv

# Just list repositories without analyzing (useful for testing)
python3 analyze_org_repos.py johndoe --skip-analysis

# Analyze only public repositories for a user
python3 analyze_org_repos.py johndoe --public-only

# Analyze only private repositories for an organization
python3 analyze_org_repos.py mycompany --private-only
```

### Using the Setup Helper
```bash
# Interactive setup and guidance
./setup_org_analysis.sh

# Test access to an organization or user
./setup_org_analysis.sh --test mycompany
./setup_org_analysis.sh --test johndoe

# Run analysis with setup verification
./setup_org_analysis.sh mycompany --private-only --export-csv results.csv
./setup_org_analysis.sh johndoe --export-csv user_results.csv
```

## 📄 Sample Output

### Organization Summary Report:
```
================================================================================
ORGANIZATION SUMMARY: mycompany
================================================================================
Repositories analyzed: 25
Repositories with PRs: 23
Total pull requests: 1,247
Total merged PRs: 1,089
Organization merge rate: 87.3%

Top languages:
  JavaScript: 8 repositories
  Python: 6 repositories
  TypeScript: 5 repositories
  Go: 3 repositories
  Java: 2 repositories

PR Size Distribution (organization-wide):
  Single commit: 423 (34.9%)
  Small (2-3 commits): 512 (42.2%)
  Medium (4-10 commits): 201 (16.6%)
  Large (10+ commits): 76 (6.3%)

Average commits per PR (across all repos): 2.8

Most active repositories (by PR count):
  web-frontend: 234 PRs, 198 merged
  api-service: 187 PRs, 165 merged
  data-pipeline: 156 PRs, 142 merged
  mobile-app: 143 PRs, 128 merged
  auth-service: 98 PRs, 87 merged
```

### CSV Export Fields:
The CSV export includes these fields for each repository:
- `repo_name`, `full_name`, `language`, `stars`, `forks`
- `total_prs`, `merged_prs`, `merge_rate`
- `avg_commits_per_pr`, `median_commits_per_pr`
- `single_commit_prs`, `small_prs`, `medium_prs`, `large_prs`
- `last_push`, `analysis_date`

## 🔧 Setup Requirements

### Prerequisites:
1. **GitHub CLI (gh)** - Install from https://cli.github.com/
2. **Python 3.6+** - Available on most systems
3. **GitHub Authentication** - Set up with proper permissions

### Authentication Setup:
```bash
# Authenticate with GitHub CLI (includes org access)
gh auth login --scopes "repo,read:org"
```

The authentication needs these permissions:
- `repo` - To access private repositories
- `read:org` - To list organization repositories

## ⚡ Performance Notes

- **Rate Limiting**: The script includes delays and timeouts to respect GitHub API limits
- **Sampling**: For repositories with many PRs, it samples the first 20 merged PRs for detailed analysis
- **Filtering**: Only analyzes repositories updated in the last year by default
- **Parallel Processing**: Each repository is analyzed sequentially to avoid rate limits

## 🔍 Troubleshooting

### Common Issues:

1. **"GitHub CLI not authenticated"**
   ```bash
   gh auth login --scopes "repo,read:org"
   ```

2. **"Cannot access organization"**
   - Verify the organization name is correct
   - Ensure you're a member of the organization
   - Check that your token has the necessary permissions

3. **"Command timed out"**
   - This can happen with very large repositories
   - The script will continue with the next repository
   - Consider using `--repo-limit` to test with fewer repositories first

4. **Rate limiting errors**
   - The script includes built-in delays
   - If you hit limits, wait and re-run the script
   - Consider reducing `--limit` to analyze fewer PRs per repository

## 📈 Use Cases

### For Engineering Managers:
- Understand development workflow patterns across teams
- Identify repositories with different PR practices
- Track merge rates and development velocity
- Plan process improvements based on data

### For DevOps/Platform Teams:
- Audit development practices across the organization
- Identify repositories that might benefit from different workflows
- Understand language and technology distribution
- Plan tooling and infrastructure improvements

### For Engineering Teams:
- Compare your repository's practices with organization norms
- Understand what "typical" PR sizes look like
- Identify opportunities for process improvements
- Track progress on development workflow changes

## 🎯 Next Steps

1. **Run your first analysis**: Start with `./setup_org_analysis.sh`
2. **Export to CSV**: Use the data in spreadsheets for custom analysis
3. **Schedule regular analysis**: Consider running monthly to track trends
4. **Share insights**: Use the summary reports to discuss development practices

---

The analysis respects GitHub API limits and handles private repositories securely.
