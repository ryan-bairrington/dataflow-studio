# Contributing to DataFlow Studio

Thank you for your interest in contributing! 🎉

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- uv (Python package manager)

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt

# Run the dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Development server
npm test         # Run tests
npm run build    # Production build
```

## Code Style

### Python
- Use [ruff](https://github.com/astral-sh/ruff) for linting
- Follow PEP 8
- Use type hints
- Docstrings for public functions/classes

### TypeScript
- Use ESLint + Prettier
- Prefer functional components with hooks
- Use TypeScript strict mode

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Run all tests to ensure they pass
6. Submit a pull request

## Adding New Node Types

See [docs/DEVELOPER.md](docs/DEVELOPER.md) for detailed instructions on:
- Creating new node classes
- Registering nodes
- Adding frontend definitions
- Writing tests

## Reporting Issues

Please include:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Browser/OS version

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
