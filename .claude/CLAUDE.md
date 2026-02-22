# ThreadMesh Project Configuration

## Behavior Rules

1. **Do nothing without explicit approval.** Do not take any action or proceed with any step unless the user has said it is okay.

2. **Stop immediately on "no".** If the user says no or rejects a tool use, stop completely. Do not retry, rephrase, or find a workaround. Wait for direction. No exceptions.

3. **Minimize LLM-based tool usage.** Use direct tools (Read, Write, Grep, Glob, Edit, Bash) freely — they are fast and cheap. Avoid spawning Task agents unless clearly necessary and explicitly approved.

## ThreadMesh-Specific Guidelines

### AGPL Licensing Requirements

- All dependencies must be AGPL-compatible (AGPL, GPL, LGPL, MIT, Apache 2.0, BSD, ISC, and other permissive/copyleft licenses)
- Before adding any package to `requirements.txt`, verify its license is compatible
- Document license compatibility decisions in code reviews
- Do not add commercial or proprietary dependencies

### Code Standards

- Use Python 3.8+ features
- Keep `main.py` as the single entry point
- All functionality must be compatible with AGPL distribution
- Test that the project can be redistributed and modified freely by others

### Project Structure

- `main.py` - Primary application logic
- `setup.py` - Package configuration with AGPL license declaration
- `requirements.txt` - AGPL-compatible dependencies only
- `README.md` - Usage and license information
- `COPYING` - Full AGPL v3 license text (when added)

## Development Workflow

- Ask for approval before adding external dependencies
- Verify license compatibility of any new package
- Keep the tool focused and avoid feature creep
- Maintain clear separation between user-facing code and utilities
