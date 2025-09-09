# Contributing to Document Normalizer

Thank you for your interest in contributing to Document Normalizer! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

This project follows a standard code of conduct:
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers and beginners
- Report any unacceptable behavior

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- Virtual environment (recommended: uv)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YutaPuta/document-normalizer.git
   cd document-normalizer
   ```

2. **Set up Environment**
   ```bash
   # Create virtual environment
   uv venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate   # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install development tools
   pip install pytest black isort flake8
   ```

3. **Verify Setup**
   ```bash
   # Run basic tests
   python simple_test.py
   python test_with_text.py
   
   # Validate documentation
   python scripts/update_docs.py --validate-only
   ```

## 🔄 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Use descriptive commit messages

### 3. Test Your Changes
```bash
# Run all tests
python simple_test.py
python detailed_test.py
python test_with_text.py

# Test with PDF
python create_sample_pdf.py
python pdf_test.py

# Validate documentation
python scripts/update_docs.py --validate-only
```

### 4. Pre-commit Checks
The project has automated pre-commit hooks that will:
- Check for documentation updates
- Validate code changes
- Ensure consistency

If warnings appear, address them before committing.

### 5. Submit Pull Request
- Push your branch to GitHub
- Create a pull request with detailed description
- Respond to review feedback

## 📏 Coding Standards

### Python Style
- **Formatting**: Use `black` for code formatting
- **Import Sorting**: Use `isort` for import organization
- **Linting**: Follow `flake8` guidelines
- **Line Length**: Maximum 127 characters
- **Naming**: Use descriptive variable and function names

### Code Organization
```python
# Good: Descriptive function names
def parse_japanese_date(date_string: str) -> str:
    """Convert Japanese era date to ISO format."""
    pass

def extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice number from document text."""
    pass
```

### Configuration Style
```yaml
# YAML: Use consistent indentation and structure
mappings:
  field_name:
    from: ["source_field1", "source_field2"]
    transform: ["trim", "normalize_japanese"]
    required: true
```

## 🧪 Testing Guidelines

### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Component interaction testing
3. **End-to-End Tests**: Complete pipeline testing
4. **Documentation Tests**: Documentation consistency

### Adding New Tests
When adding features:

1. **Create test cases** in appropriate test file
2. **Test edge cases** and error conditions
3. **Include Japanese text samples** for localization features
4. **Verify documentation** is updated

### Test File Structure
```python
def test_new_feature():
    """Test description with expected behavior."""
    # Arrange
    input_data = "test input"
    expected_output = "expected result"
    
    # Act
    result = new_feature(input_data)
    
    # Assert
    assert result == expected_output
```

## 📚 Documentation

### Documentation Requirements
- **Code Changes**: Update relevant documentation
- **New Features**: Add usage examples and configuration
- **API Changes**: Update API documentation
- **Breaking Changes**: Highlight in CHANGELOG and migration guide

### Documentation Structure
```
doc/
├── LOCAL_TESTING.md      # Setup and testing guide
├── JAPANESE_PROCESSING.md # Japanese text processing
├── CONFIGURATION.md       # Configuration reference
├── AZURE_DEPLOYMENT.md    # Production deployment
└── HOOKS_GUIDE.md        # Development hooks
```

### Automatic Documentation
The project includes automatic documentation synchronization:
- Pre-commit hooks validate documentation consistency
- `scripts/update_docs.py` can auto-update documentation
- CI/CD checks ensure documentation completeness

## 🔄 Pull Request Process

### 1. PR Requirements
- [ ] **Tests**: All tests pass locally
- [ ] **Documentation**: Updated for changes
- [ ] **Code Style**: Follows project standards
- [ ] **Description**: Clear explanation of changes
- [ ] **Breaking Changes**: Clearly marked if any

### 2. PR Template
Use the provided PR template to ensure all information is included:
- Summary of changes
- Type of change (bug fix, feature, etc.)
- Testing performed
- Documentation updates
- Related issues

### 3. Review Process
1. **Automated Checks**: CI/CD pipeline runs
2. **Code Review**: Maintainer review
3. **Testing**: Feature testing in various scenarios
4. **Documentation Review**: Ensure consistency
5. **Approval**: Final approval and merge

### 4. After Merge
- Monitor CI/CD pipeline
- Check for any production issues
- Update related issues and project board

## 🎯 Types of Contributions

### 🐛 Bug Fixes
- Use issue template for bug reports
- Include reproduction steps
- Add regression tests
- Update documentation if needed

### ✨ New Features
- Discuss in issues before large changes
- Follow existing architectural patterns
- Add comprehensive tests
- Update all relevant documentation

### 📚 Documentation Improvements
- Fix typos and unclear sections
- Add examples and use cases
- Improve formatting and structure
- Translate to additional languages

### 🔧 Infrastructure
- CI/CD improvements
- Development tooling
- Performance optimizations
- Security enhancements

## 🌏 Japanese Language Support

This project specifically supports Japanese document processing:

### When Contributing Japanese Features
- **Test with real Japanese text** samples
- **Include era conversion** tests (令和, 平成, etc.)
- **Handle full-width characters** properly
- **Consider cultural context** in business documents
- **Add Japanese examples** to documentation

### Cultural Considerations
- Japanese business document formats
- Date and number formatting conventions
- Company name patterns and variations
- Address and contact information formats

## 🏷️ Issue Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to docs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `japanese-processing` - Related to Japanese text processing
- `azure-functions` - Related to Azure Functions integration
- `configuration` - Related to YAML configuration system

## 📞 Getting Help

### Resources
- **Documentation**: Check the `doc/` directory
- **Examples**: Look at existing test files
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions

### Contact
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Pull Requests**: For code contributions

## 🙏 Recognition

Contributors will be:
- Listed in the repository contributors
- Mentioned in release notes for significant contributions
- Added to the project README for major features

Thank you for contributing to Document Normalizer! 🎉