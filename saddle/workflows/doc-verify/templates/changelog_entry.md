# CHANGELOG Entry Template

Use this template when adding entries to CHANGELOG.md.

## Format

Follow [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
## [Unreleased]

### Added
- [New feature or capability]

### Changed
- [Modification to existing functionality]

### Deprecated
- [Feature that will be removed in future versions]

### Removed
- [Feature that was removed]

### Fixed
- [Bug fix]

### Security
- [Security-related change]
```

## Guidelines

### When to Add Entries

- **Added**: New features, new APIs, new configuration options
- **Changed**: Breaking changes, behavior modifications, dependency updates
- **Deprecated**: Features marked for removal (with migration path)
- **Removed**: Features that were deprecated and now removed
- **Fixed**: Bug fixes, performance improvements
- **Security**: Security patches, vulnerability fixes

### Writing Good Entries

1. **Be specific**: "Fixed null pointer in auth module" not "Fixed bug"
2. **User-focused**: Describe impact, not implementation details
3. **Link issues**: Reference issue numbers when applicable
4. **Include migration**: For breaking changes, explain how to adapt

## Examples

### Feature Addition

```markdown
### Added
- User authentication via OAuth 2.0 with Google and GitHub providers
- Rate limiting for API endpoints (configurable per-route)
- Export functionality for user data in CSV and JSON formats
```

### Breaking Change

```markdown
### Changed
- **BREAKING**: Renamed `get_user()` to `fetch_user()` for consistency
  - Migration: Update all calls from `get_user(id)` to `fetch_user(id)`
- Updated minimum Python version to 3.9 (was 3.8)
```

### Bug Fix

```markdown
### Fixed
- Race condition in concurrent payment processing (#123)
- Memory leak in WebSocket connection handler
- Incorrect timezone handling in scheduled tasks
```

### Security Update

```markdown
### Security
- Patched XSS vulnerability in user profile display (CVE-2024-XXXX)
- Updated dependencies to address known vulnerabilities
```

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Example version history:

```markdown
## [2.0.0] - 2024-03-15
### Changed
- **BREAKING**: New authentication API

## [1.2.0] - 2024-02-01
### Added
- Export functionality

## [1.1.1] - 2024-01-15
### Fixed
- Login timeout issue
```
