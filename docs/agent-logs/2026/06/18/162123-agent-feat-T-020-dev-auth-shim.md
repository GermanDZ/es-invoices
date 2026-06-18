# Agent Run Log: T-020 Dev Auth Shim

**Branch:** feat/T-020-dev-auth-shim  
**Task:** T-020  
**Phase:** construction  

## Execution Window
- **Start:** 2026-06-18T16:10:37Z
- **End:** 2026-06-18T16:21:23Z

## Commits
- fbee179: feat(devtools): add DEBUG-gated dev login shim + seed command
- 6d81934: docs(T-020): operations checklist, design notes, verification grade
- 6da8e14: docs(T-020): add roadmap row + sync derived views + status note

## Files Changed
```
config/settings.py
config/urls.py
devtools/__init__.py
devtools/apps.py
devtools/owner.py
devtools/views.py
devtools/urls.py
devtools/management/__init__.py
devtools/management/commands/__init__.py
devtools/management/commands/seed_dev_owner.py
devtools/tests/__init__.py
devtools/tests/test_dev_login.py
devtools/tests/urls.py
docs/changes/T-020/plan.md
docs/changes/T-020/design.md
docs/roadmap.md
docs/project-status.md
docs/status-notes/2026-06-18-T-020.md
```

## Decisions
- DEBUG-gated devtools app with double-guard (INSTALLED_APPS + view-level settings.DEBUG) ensures zero production auth surface
- Dedicated test urlconf (devtools/tests/urls.py) works around Django test-runner forcing DEBUG=False at urlconf-load
- Explicit ModelBackend passed to login() since seeded user never went through authenticate()
- No models/migrations used; idempotent get_or_create seed

## Verification
- 129 tests pass
- 2 Postgres-gated skips
