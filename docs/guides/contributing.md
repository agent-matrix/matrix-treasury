# Contributing Guidelines

Thank you for your interest in contributing to Matrix Treasury!

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### 1. Find an Issue

- Check [GitHub Issues](https://github.com/agent-matrix/matrix-treasury/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Or propose a new feature/fix

### 2. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/matrix-treasury.git
cd matrix-treasury
git remote add upstream https://github.com/agent-matrix/matrix-treasury.git
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `test/` - Tests
- `refactor/` - Code refactoring

### 4. Make Changes

Follow our [coding standards](development.md#coding-standards).

### 5. Test Your Changes

```bash
# Backend tests
make test

# Frontend tests
cd frontend && npm test

# Ensure all tests pass!
```

### 6. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: Add multi-signature wallet support"
git commit -m "fix: Resolve race condition in balance updates"
git commit -m "docs: Update API documentation"
```

Commit message format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Pull Request Guidelines

### PR Title

Use conventional commit format:

```
feat: Add support for EUR currency
fix: Resolve authentication token expiry bug
```

### PR Description

Include:

1. **What**: What does this PR do?
2. **Why**: Why is this change needed?
3. **How**: How does it work?
4. **Testing**: How was it tested?

Template:

```markdown
## Description
Brief description of the changes.

## Motivation
Why is this change needed?

## Changes
- List key changes
- One per line

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Closes #123
```

### Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts
- [ ] PR description is complete

## Development Setup

See [Development Guide](development.md) for complete setup instructions.

Quick start:

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-upgrade.txt
make install
make dev

# Frontend
cd frontend
npm install
npm run dev
```

## Code Review Process

### What We Look For

1. **Correctness**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Performance**: Is it efficient?
4. **Security**: Are there security implications?
5. **Style**: Does it follow our conventions?
6. **Documentation**: Is it well-documented?

### Review Timeline

- Initial review: Within 2-3 business days
- Follow-up reviews: Within 1-2 business days
- Merge: After approval from 2 maintainers

### Addressing Review Comments

```bash
# Make changes
git add .
git commit -m "fix: Address review comments"
git push origin feature/your-feature-name
```

## Coding Standards

### Python

- Follow PEP 8
- Use type hints
- Write docstrings
- Max line length: 100 characters

```python
def calculate_balance(agent_id: str, currency: str = "USDC") -> float:
    """Calculate agent balance in specified currency.

    Args:
        agent_id: Unique agent identifier
        currency: Currency code (default: USDC)

    Returns:
        float: Current balance

    Raises:
        AgentNotFoundError: If agent doesn't exist
    """
    pass
```

### TypeScript

- Use TypeScript strict mode
- Define interfaces for all data structures
- Use functional components
- Prefer hooks over classes

```typescript
interface Agent {
  id: string;
  email: string;
  balance: number;
}

function AgentCard({ agent }: { agent: Agent }) {
  return <div>{agent.email}: ${agent.balance}</div>;
}
```

### Git Commit Messages

```
feat(treasury): Add EUR currency support

- Add EUR vault implementation
- Update balance calculations
- Add EUR to frontend dropdown

Closes #456
```

## Testing Requirements

### Unit Tests

Required for:
- All new functions
- All bug fixes
- All business logic

```python
def test_new_feature():
    result = new_feature()
    assert result == expected
```

### Integration Tests

Required for:
- New API endpoints
- Database changes
- Authentication changes

### Coverage

Maintain >80% code coverage.

```bash
# Check coverage
pytest --cov=src
```

## Documentation

### Code Documentation

- Python: Use docstrings (Google style)
- TypeScript: Use JSDoc comments

### User Documentation

Update docs for:
- New features
- API changes
- Configuration changes
- Breaking changes

Location: `docs/`

## Security

### Reporting Vulnerabilities

**Do not** open public issues for security vulnerabilities.

Email: security@ruslanmv.com

### Security Checklist

- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Authentication/authorization checks

## Release Process

Maintainers handle releases:

1. Update version in `pyproject.toml` and `package.json`
2. Update CHANGELOG.md
3. Create release branch
4. Tag release
5. Deploy to production

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **Discord**: https://discord.gg/AJUnEerk
- **Email**: contact@ruslanmv.com

### Getting Help

- Read the [documentation](../README.md)
- Search existing [issues](https://github.com/agent-matrix/matrix-treasury/issues)
- Ask on [Discord](https://discord.gg/AJUnEerk)
- Email: contact@ruslanmv.com

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Thanked on Discord

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Questions?

Feel free to ask questions:
- Open a discussion on GitHub
- Ask in Discord
- Email the maintainers

Thank you for contributing to Matrix Treasury! 🚀
