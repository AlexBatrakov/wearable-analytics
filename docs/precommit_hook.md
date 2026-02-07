# Local pre-commit hook (data safety)

This repo keeps raw Garmin exports locally under data/raw/DI_CONNECT. These files must never be committed.

Create a local git pre-commit hook that blocks staging those paths:

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh

if git diff --cached --name-only | grep -E '^(data/raw/|.*DI_CONNECT/)' >/dev/null; then
  echo "Error: Garmin export data cannot be committed. Remove files from staging."
  exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

Notes:
- git hooks are local-only and not committed to the repository.
- If you need additional guardrails, consider server-side hooks in your remote.
