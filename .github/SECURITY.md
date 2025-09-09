# Security Policy

## 🔒 Supported Versions

We actively support the following versions of Document Normalizer with security updates:

| Version | Supported          |
| ------- | ------------------ |
| main    | ✅ Yes             |
| v1.0.x  | ✅ Yes             |

## 🚨 Reporting a Vulnerability

We take the security of Document Normalizer seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### 📧 How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. **Email**: Send details to the project maintainer
2. **Private Security Advisory**: Use GitHub's private vulnerability reporting feature
3. **Direct Contact**: Contact the project maintainer directly

### 📋 What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Affected versions** (if known)
- **Any possible workarounds**
- **Your contact information** for follow-up

### ⏱️ Response Timeline

We aim to respond to security reports within:
- **Initial response**: 48 hours
- **Confirmation**: 7 days
- **Fix and disclosure**: 30 days (depending on complexity)

## 🔐 Security Considerations

### Data Handling
Document Normalizer processes sensitive business documents. Key security considerations:

#### PDF Processing
- **Input Validation**: All PDF inputs are validated before processing
- **Memory Management**: Proper cleanup of PDF content in memory
- **Malware Prevention**: PDF processing is sandboxed

#### Azure Integration
- **Authentication**: Secure API key management
- **Encryption**: All data transmitted to Azure services is encrypted
- **Access Control**: Least privilege access to Azure resources

#### Data Storage
- **Temporary Data**: Automatically cleaned up after processing
- **Persistent Storage**: Encrypted at rest in Azure
- **Access Logs**: Comprehensive logging for audit trails

### Configuration Security

#### API Keys and Secrets
- **Environment Variables**: Store sensitive configuration in environment variables
- **Key Vault Integration**: Use Azure Key Vault for production secrets
- **Rotation**: Regular rotation of API keys and credentials

#### YAML Configuration
- **Validation**: All YAML configurations are validated
- **Injection Prevention**: No dynamic code execution from configuration
- **Access Control**: Configuration files have appropriate permissions

### Deployment Security

#### Azure Functions
- **HTTPS Only**: All endpoints require HTTPS
- **Authentication**: Configure appropriate authentication mechanisms
- **Network Security**: Use VNet integration where applicable
- **Monitoring**: Enable Application Insights for security monitoring

#### Local Development
- **Environment Isolation**: Use virtual environments
- **Secret Management**: Never commit secrets to version control
- **Development Keys**: Use separate keys for development and production

## 🛡️ Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version
2. **Secure Configuration**: Follow security configuration guidelines
3. **Monitor Logs**: Regularly review application logs
4. **Access Control**: Implement proper access controls
5. **Data Classification**: Classify and handle documents appropriately

### For Contributors

1. **Security Review**: Consider security implications of code changes
2. **Dependency Updates**: Keep dependencies updated
3. **Input Validation**: Validate all external inputs
4. **Error Handling**: Don't expose sensitive information in errors
5. **Testing**: Include security test cases

## 🔍 Known Security Considerations

### PDF Processing
- **Complex Parsing**: PDF parsing can be complex and prone to issues
- **Memory Usage**: Large PDFs may consume significant memory
- **Content Validation**: Document content should be validated

### Japanese Text Processing
- **Character Encoding**: Proper handling of various Japanese encodings
- **Input Sanitization**: Sanitize Japanese text input
- **Pattern Matching**: Secure regex patterns for Japanese text

### Azure Services
- **Rate Limiting**: Implement appropriate rate limiting
- **Error Handling**: Handle Azure service errors securely
- **Data Retention**: Follow data retention policies

## 🔄 Security Updates

### Notification Process
When security updates are available:

1. **Security Advisory** published on GitHub
2. **Release Notes** include security fix details
3. **Migration Guide** provided for breaking changes
4. **Documentation** updated with security recommendations

### Update Process
To apply security updates:

1. **Review** the security advisory
2. **Test** the update in a development environment
3. **Deploy** to production following deployment guidelines
4. **Verify** the security fix is properly applied

## 📋 Security Checklist

### Pre-deployment Checklist
- [ ] All secrets stored in secure configuration
- [ ] HTTPS enabled for all endpoints
- [ ] Input validation implemented
- [ ] Error handling doesn't expose sensitive data
- [ ] Logging configured for security events
- [ ] Access controls properly configured
- [ ] Dependencies updated to latest secure versions

### Production Monitoring
- [ ] Monitor for unusual processing patterns
- [ ] Review access logs regularly
- [ ] Monitor Azure service quotas and limits
- [ ] Track processing errors and failures
- [ ] Monitor for potential data exfiltration

## 🏷️ Security Labels

GitHub issues related to security use these labels:
- `security` - General security-related issues
- `vulnerability` - Confirmed security vulnerabilities
- `security-enhancement` - Security improvements
- `audit` - Security audit findings

## 📚 Additional Resources

### Security Documentation
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/)
- [Python Security Guidelines](https://python.org/dev/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Security Tools
- **Bandit**: Python security linter (included in CI/CD)
- **Safety**: Dependency vulnerability scanner (included in CI/CD)
- **Azure Security Center**: For Azure resource monitoring

## ⚠️ Disclaimer

While we make every effort to ensure the security of Document Normalizer, users are responsible for:
- Proper configuration and deployment
- Securing their Azure environment
- Following security best practices
- Regular monitoring and maintenance

This software is provided "as is" without warranty of any kind. See the LICENSE file for full terms.