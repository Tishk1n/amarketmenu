# System Patterns

## Coding Standards
- Follow PEP 8 style guide for Python code
- Use async/await patterns consistently with Aiogram
- Document all functions and classes with docstrings
- Use type hints where appropriate

## Architecture Patterns
- Use dispatcher pattern for handling bot commands and callbacks
- Implement repository pattern for database access
- Separate concerns: handlers, services, data access

## Project Structure
```
amarketmenu/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   └── user.py
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── admin_kb.py
│   │   └── menu_kb.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth.py
│   └── utils/
│       ├── __init__.py
│       └── db.py
├── config.py
├── database/
│   ├── __init__.py
│   └── models.py
├── main.py
└── requirements.txt
```

## Testing Strategy
- Unit tests for critical business logic
- Integration tests for database operations
- Manual testing for UI/UX elements

[2025-06-01 11:41] - Initial system patterns defined
