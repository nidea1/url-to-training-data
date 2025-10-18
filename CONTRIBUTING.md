# Contributing to Content to Training Data

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/nidea1/content-to-training-data/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Step-by-step reproduction instructions
   - Expected vs actual behavior
   - Python version and OS information
   - Error messages/logs

### Suggesting Enhancements

1. Use the [Issues](https://github.com/nidea1/content-to-training-data/issues) tab
2. Describe the enhancement clearly
3. Explain the use case and expected benefit
4. Provide code examples if applicable

### Submitting Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/nidea1/content-to-training-data.git
   cd content-to-training-data
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow PEP 8 style guide
   - Add comments for complex logic
   - Update docstrings
   - Test your code

4. **Commit with clear messages**
   ```bash
   git commit -m "Add: Brief description of changes"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Provide a clear description
   - Reference related issues
   - Include any relevant screenshots/examples

## Development Setup

1. **Clone and setup virtual environment**
   ```bash
   git clone https://github.com/nidea1/content-to-training-data.git
   cd content-to-training-data
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov  # For testing
   ```

3. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Add your GOOGLE_API_KEY
   ```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where applicable
- Write descriptive variable/function names
- Maximum line length: 100 characters (where reasonable)
- Add docstrings to functions and classes

### Example Function

```python
def chunk_by_headings(
    text: str,
    min_level: int = 2,
    debug: bool = False
) -> List[str]:
    """
    Split text by markdown headings.
    
    Args:
        text: Input markdown text
        min_level: Minimum heading level (1-6)
        debug: Enable debug logging
        
    Returns:
        List of text chunks
        
    Raises:
        ValueError: If min_level is not between 1-6
    """
    # Implementation...
    pass
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for reasonable code coverage

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## Documentation

- Update README.md if adding features
- Add docstrings to all public functions/classes
- Include usage examples
- Document configuration options

## Priority Areas for Contribution

### High Priority
- [ ] Unit tests and test coverage
- [ ] Bug fixes
- [ ] Performance improvements
- [ ] Documentation improvements

### Medium Priority
- [ ] New scraping strategies
- [ ] New cleaning strategies
- [ ] Error handling improvements
- [ ] Logging enhancements

### Nice to Have
- [ ] Web UI
- [ ] Additional API provider support
- [ ] Docker configuration
- [ ] CI/CD pipeline

## Commit Messages

Use clear, descriptive commit messages:

```
Add: New feature description
Fix: Bug description
Refactor: Code reorganization description
Docs: Documentation update description
Test: Test addition/modification description
Perf: Performance improvement description
```

## Review Process

1. Automated checks will run (if configured)
2. Project maintainers will review your PR
3. Address feedback and make requested changes
4. Your PR will be merged once approved

## Questions?

- Open an issue for questions
- Check existing documentation
- Review similar code in the repository

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to make this project better!** 🎉
