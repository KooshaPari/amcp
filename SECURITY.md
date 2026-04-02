# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of **AgentMCP** seriously. If you discover a security vulnerability, please do NOT open a public issue. Instead, report it privately.

### What to include

- A detailed description of the vulnerability
- Steps to reproduce (proof of concept)
- Potential impact
- Any suggested fixes or mitigations

We will acknowledge your report within 48 hours.

## Security Considerations

When using AgentMCP:

- **API Keys**: Never commit API keys to version control
- **Resource Access**: MCP resources are access-controlled
- **Database Connections**: Use TLS for database connections
- **Agent Permissions**: Configure appropriate agent permissions

## Dependency Scanning

AgentMCP regularly scans dependencies for vulnerabilities:

- `pip-audit` for Python dependencies
- Safety DB for known vulnerabilities
- Automated dependency updates

---

Thank you for helping keep the community secure!
