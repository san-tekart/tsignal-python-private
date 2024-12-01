# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-26

### Added
- Initial release
- Basic signal-slot mechanism with decorators
- Support for both synchronous and asynchronous slots
- Thread-safe signal emissions
- Automatic connection type detection
- Comprehensive test suite
- Full documentation

## [0.1.1] - 2024-12-01

### Changed
- Refactored signal connection logic to support direct function connections.
- Improved error handling for invalid connections.
- Enhanced logging for signal emissions and connections.

### Fixed
- Resolved issues with disconnecting slots during signal emissions.
- Fixed bugs related to async slot processing and connection management.

### Removed
- Deprecated unused constants and methods from the core module.
