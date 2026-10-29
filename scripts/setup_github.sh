#!/usr/bin/env bash
# Sets up the GitHub repository in one command.
#   bash scripts/setup_github.sh owner/repo            description, topics, Discussions, labels, milestone, seed issues
#   PROTECT_MAIN=1 bash scripts/setup_github.sh ...   also protects main with the book checks and CODEOWNERS review
# Idempotent: safe to run more than once.
set -euo pipefail
REPO="${1:?Usage: bash scripts/setup_github.sh owner/repo}"
cd "$(dirname "$0")/.."
command -v gh >/dev/null || { echo "Install GitHub CLI: https://cli.github.com" >&2; exit 3; }
gh auth status >/dev/null || { echo "Run: gh auth login" >&2; exit 3; }

echo "1/6 Description, homepage and topics"
gh repo edit "$REPO" \
  --description "From Black Box to Evidence · De la caja negra a la evidencia — modernizing COBOL beyond translation. Open book (EN/ES) and runnable lab." \
  --homepage "https://jmfloreszazo.com" \
  --enable-issues --enable-discussions \
  --add-topic cobol --add-topic mainframe --add-topic modernization --add-topic legacy-modernization \
  --add-topic agentic-ai --add-topic test-oracles --add-topic dotnet --add-topic software-architecture \
  --add-topic c4-model --add-topic mermaid --add-topic open-book

echo "2/6 Labels"
python3 - "$REPO" <<'PY'
import json, subprocess, sys
for l in json.load(open('.github/labels.json', encoding='utf-8')):
    subprocess.run(['gh', 'label', 'create', l['name'], '--repo', sys.argv[1], '--color', l['color'],
                    '--description', l['description'], '--force'], check=True, stdout=subprocess.DEVNULL)
print('   ok')
PY

echo "3/6 Private vulnerability reporting"
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" >/dev/null 2>&1 \
  && echo "   ok" || echo "   not available: enable it in Settings → Security"

echo "4/6 Milestone"
python3 - "$REPO" <<'PY'
import json, subprocess, sys
repo, seed = sys.argv[1], json.load(open('.github/seed-issues.json', encoding='utf-8'))
existing = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/milestones?state=all&per_page=100']))
if seed['milestone']['title'] not in [m['title'] for m in existing]:
    subprocess.run(['gh', 'api', f'repos/{repo}/milestones', '-f', f"title={seed['milestone']['title']}",
                    '-f', f"description={seed['milestone']['description']}"], check=True, stdout=subprocess.DEVNULL)
print('   ok')
PY

echo "5/6 Seed issues"
python3 - "$REPO" <<'PY'
import json, subprocess, sys
repo, seed = sys.argv[1], json.load(open('.github/seed-issues.json', encoding='utf-8'))
titles = {i['title'] for i in json.loads(subprocess.check_output(
    ['gh', 'issue', 'list', '--repo', repo, '--state', 'all', '--limit', '500', '--json', 'title']))}
created = 0
for issue in seed['issues']:
    if issue['title'] in titles:
        continue
    cmd = ['gh', 'issue', 'create', '--repo', repo, '--title', issue['title'], '--body', issue['body'],
           '--milestone', issue['milestone']]
    for label in issue['labels']:
        cmd += ['--label', label]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    created += 1
print(f'   {created} created, {len(seed["issues"]) - created} already existed')
PY

echo "6/6 Protecting main"
if [ "${PROTECT_MAIN:-0}" = "1" ]; then
  gh api -X PUT "repos/$REPO/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["links, es/en sync, generated files", "markdown", "diagrams"] },
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 1, "require_code_owner_reviews": true },
  "restrictions": null
}
JSON
  echo "   ok (the maintainer can bypass it as admin)"
else
  echo "   skipped: run with PROTECT_MAIN=1 after the first green push"
fi
echo "Done: https://github.com/$REPO"
