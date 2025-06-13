# ReadmeForge

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies](#technologies)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Optimization](#optimization)
- [Contributing](#contributing)
- [License](#license)

## Overview

**ReadmeForge** is a Python tool for automatically generating professional README files based on project analysis. It scans your project structure, identifies technologies used, and creates a comprehensive README.md tailored to your project's specific characteristics.

The application is built using Clean Architecture principles to ensure high testability, maintainability, and scalability. It separates business logic from technical implementations and provides a flexible template system for README generation.

### Target Audience
- Software Developers
- Open Source Contributors
- Project Maintainers
- Development Teams

## Features

### Project Analysis

- **Technology Detection**: Automatically identifies programming languages and frameworks
- **Structure Analysis**: Maps and documents your project's file organization
- **Dependency Recognition**: Lists project dependencies from package files
- **License Detection**: Identifies and includes license information

### README Generation

- **Template-Based**: Multiple README templates for different project types
- **Section Customization**: Include or exclude specific README sections
- **Formatting Options**: Generate in Markdown, HTML, or plain text
- **Preview Capability**: View generated README before saving

### Configuration

- **Custom Templates**: Create and use your own README templates
- **Section Control**: Configure which sections appear in your README
- **Output Options**: Specify output location and format
- **Analysis Rules**: Define custom rules for project analysis

### Integration

- **CLI Interface**: Easy command-line usage
- **Git Integration**: Extract repository information
- **CI/CD Ready**: Can be integrated into continuous integration workflows
- **Extensible Design**: Plugin system for custom analyzers

## Technologies

### Development

- **Python**: Primary programming language
- **Jinja2**: Template rendering engine
- **Click**: Command-line interface framework
- **PyYAML**: YAML configuration parsing
- **GitPython**: Git repository analysis
- **Markdown**: Markdown processing

### Architecture

- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Repository Pattern**: Abstract data access
- **Dependency Injection**: Loose coupling between components
- **Use Case Pattern**: Application business rules encapsulation

## Architecture

ReadmeForge is built on Clean Architecture principles with three main layers:

1. **Domain Layer**: Core business logic and rules
   - Entities: Core data structures
   - Use Cases: Application-specific business rules
   - Ports: Interface definitions for external dependencies

2. **Interface Layer**: User interaction handling
   - CLI: Command-line interface implementation
   - API: (Future) Programmatic access points

3. **Infrastructure Layer**: Technical implementations
   - Repositories: Data access implementations
   - Analyzers: Project analysis tools
   - Templates: README template implementations

## Installation

### Prerequisites

- Python 3.8+
- Git (for repository analysis features)

### Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/takeshikodev/readmeforge.git
   cd readmeforge
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python main.py [PROJECT_PATH] (Optional: --template [standard, minimal, detailed] --output [PATH] --section [INCLUDE_SECTION])
   ```

## Configuration

Configuration is managed through `config.json` in the project root:

```json
{
  "templates": {
    "default": "standard",
    "available": ["standard", "minimal", "detailed"]
  },
  "sections": {
    "standard": [
      "overview",
      "features",
      "technologies",
      "architecture",
      "installation",
      "configuration",
      "project_structure",
      "optimization",
      "contributing",
      "license"
    ]
  }
}
```

### Configuration Parameters

- **templates.default**: Default template to use
- **templates.available**: List of available templates
- **sections**: Section configurations for each template type

## Project Structure

```
readmeforge/
├── src/                  # Source code
│   ├── domain/           # Business logic layer
│   │   ├── entities/     # Core data structures
│   │   ├── ports/        # Interface definitions
│   │   └── usecases/     # Application business rules
│   ├── interfaces/       # User interfaces
│   │   └── cli/          # Command-line interface
│   └── infrastructure/   # Implementation details
│       ├── analyzers/    # Project analysis tools
│       ├── repositories/ # Data access implementations
│       └── templates/    # README templates
├── config.json           # Configuration
├── requirements.txt      # Dependencies
├── LICENSE               # License information
├── README.md             # Documentation
└── main.py               # Entry point
```

## Optimization

- Template caching for faster generation
- Efficient project scanning with file type filtering
- Parallelized analysis for large projects
- Incremental analysis for repeated runs

## Contributing

If you want to contribute to the project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a Pull Request

Please ensure your code follows the project's architecture and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Takeshiko 
