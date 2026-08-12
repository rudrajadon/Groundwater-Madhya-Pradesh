# Contributing to Groundwater Forecast System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/groundwater-app.git
   cd groundwater-app
   ```
3. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Full Stack (Docker)
```bash
cd infra
docker-compose up -d
```

## 📝 Coding Standards

### Python (Backend)
- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and under 50 lines when possible

Example:
```python
async def get_well_forecast(well_id: str) -> ForecastResponse:
    """
    Get 12-month forecast for a specific well.
    
    Args:
        well_id: Unique well identifier
        
    Returns:
        ForecastResponse with predictions and metadata
    """
    pass
```

### TypeScript/React (Frontend)
- Use TypeScript for all new code
- Follow functional component patterns with hooks
- Use explicit types, avoid `any`
- Keep components under 200 lines
- Extract reusable logic into custom hooks

Example:
```typescript
interface WellMapProps {
  onWellSelect: (wellId: string, district: string) => void;
  center?: [number, number];
}

export default function WellMap({ onWellSelect, center }: WellMapProps) {
  // Component implementation
}
```

## ✅ Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🔍 Code Review Process

1. **Self-review** your changes before submitting
2. **Write clear commit messages**:
   ```
   feat: Add district summary report generation
   
   - Implements PDF generation for district-wide summaries
   - Adds endpoint /api/v1/exports/district
   - Includes statistics for all wells in district
   ```
3. **Create a Pull Request** with:
   - Clear description of changes
   - Screenshots for UI changes
   - Link to related issues
   - List of breaking changes (if any)

## 🐛 Reporting Bugs

Create an issue with:
- Clear title describing the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/logs if applicable
- Environment (OS, browser, versions)

## 💡 Suggesting Features

Create an issue with:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Mock-ups or examples (if applicable)

## 📦 Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console errors or warnings
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

## 🔒 Security

If you discover a security vulnerability, please email the maintainers directly instead of creating a public issue.

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be acknowledged in the README.md file.

Thank you for contributing! 🎉
