"""Module with a class for rendering templates."""
import os
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ...domain.ports.templates import TemplateRendererPort
from ...domain.ports.repositories import FileRepositoryPort, ConfigRepositoryPort


class TemplateRenderer(TemplateRendererPort):
    """Class for rendering README templates."""
    
    def __init__(self, templates_dir: str, file_repository: FileRepositoryPort, 
                 config_repository: ConfigRepositoryPort):
        """
        Initialization of the template renderer.
        
        Args:
            templates_dir: The path to the directory with templates
            file_repository: Repository for working with files
            config_repository: Repository for working with configuration
        """
        self.templates_dir = templates_dir
        self.file_repository = file_repository
        self.config_repository = config_repository
        self._ensure_templates_dir_exists()
        
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'md']),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, 
               template_name: str, 
               context: Dict[str, Any],
               sections: Optional[List[str]] = None) -> str:
        """
        Renders a template with the given context.
        
        Args:
            template_name: The name of the template
            context: The data context to substitute into the template
            sections: A list of sections to include (if None, all sections are used)
        
        Returns:
            str: The rendered template
            
        Raises:
            ValueError: If the template is not found
        """
        base_template_path = f"{template_name}/base.md.j2"
        
        if sections is None:
            sections = self.get_sections_for_template(template_name)
        
        enhanced_context = context.copy()
        enhanced_context["sections"] = sections
        
        try:
            template = self.env.get_template(base_template_path)
        except Exception as e:
            raise ValueError(f"Error loading template {template_name}: {e}")
        
        return template.render(**enhanced_context)
    
    def get_available_templates(self) -> List[str]:
        """
        Returns a list of available templates.
        
        Returns:
            List[str]: A list of available template names
        """
        templates = []
        try:
            for item in os.listdir(self.templates_dir):
                if os.path.isdir(os.path.join(self.templates_dir, item)):
                    if os.path.exists(os.path.join(self.templates_dir, item, "base.md.j2")):
                        templates.append(item)
        except FileNotFoundError:
            pass
            
        return templates
    
    def get_sections_for_template(self, template_name: str) -> List[str]:
        """
        Returns a list of sections for the specified template.
        
        Args:
            template_name: The name of the template
            
        Returns:
            List[str]: A list of section names
        """
        try:
            sections_config = self.config_repository.get_config("sections")
            if template_name in sections_config:
                return sections_config[template_name]
                
            return sections_config.get("standard", [])
        except KeyError:
            return []
    
    def _ensure_templates_dir_exists(self) -> None:
        """Checks if the templates directory exists and creates it if it doesn't."""
        if not os.path.exists(self.templates_dir):
            try:
                os.makedirs(self.templates_dir)
                self._create_default_templates()
            except OSError as e:
                print(f"Error creating templates directory: {e}")
    
    def _create_default_templates(self) -> None:
        """Creates default templates if they don't exist."""
        self._create_standard_template()
        
        self._create_minimal_template()
        
        self._create_detailed_template()
    
    def _create_standard_template(self) -> None:
        """Creates a standard template."""
        standard_dir = os.path.join(self.templates_dir, "standard")
        os.makedirs(standard_dir, exist_ok=True)
        
        base_path = os.path.join(standard_dir, "base.md.j2")
        
        content = """# {{ name }}

## Table of Contents

{% for section in sections %}
{% if section != "table_of_contents" %}
- [{{ section|title|replace("_", " ") }}](#{{ section|lower|replace("_", "-") }})
{% endif %}
{% endfor %}

{% if "overview" in sections %}
## Overview

{{ description }}

{% if name is defined and '_' in name or '-' in name %}
**{{ name|replace('_', ' ')|replace('-', ' ')|title }}** - {% endif %}{% if features|length > 0 %}a tool for {{ features[0].description|lower }}{% if features|length > 1 %} and {{ features[1].description|lower }}{% endif %}.
{% else %}
{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
This project is built with {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('name') }}.
{% endif %}
{% endif %}

{% if metadata.has_documentation %}
Documentation is available in the project directory.
{% endif %}
{% endif %}

{% if "features" in sections and features %}
## Features

{% for feature in features %}
### {{ feature.name }}

{{ feature.description }}

{% endfor %}
{% endif %}

{% if "technologies" in sections %}
## Technologies

{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
### Programming Languages
{% for tech in technologies|selectattr('category', 'equalto', 'language')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'framework')|list|length > 0 %}
### Frameworks
{% for tech in technologies|selectattr('category', 'equalto', 'framework')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'frontend')|list|length > 0 or technologies|selectattr('category', 'equalto', 'backend')|list|length > 0 %}
### Front-end / Back-end
{% for tech in technologies|selectattr('category', 'equalto', 'frontend')|list %}
- **{{ tech.name }}** (Front-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% for tech in technologies|selectattr('category', 'equalto', 'backend')|list %}
- **{{ tech.name }}** (Back-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'database')|list|length > 0 %}
### Database
{% for tech in technologies|selectattr('category', 'equalto', 'database')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'devops')|list|length > 0 %}
### DevOps
{% for tech in technologies|selectattr('category', 'equalto', 'devops')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'testing')|list|length > 0 %}
### Testing
{% for tech in technologies|selectattr('category', 'equalto', 'testing')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'architecture')|list|length > 0 %}
### Architecture Patterns
{% for tech in technologies|selectattr('category', 'equalto', 'architecture')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'other')|list|length > 0 %}
### Other
{% for tech in technologies|selectattr('category', 'equalto', 'other')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}
{% endif %}

{% if "architecture" in sections %}
## Architecture

{% if metadata.architecture_description is defined %}
{{ metadata.architecture_description }}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'architecture')|list|length > 0 %}
This project uses the following architectural approaches:
{% for tech in technologies|selectattr('category', 'equalto', 'architecture')|list %}
- **{{ tech.name }}**
{% endfor %}
{% endif %}

{% if structure.tree.children|selectattr("name", "equalto", "src")|list|length > 0 %}
{% set src_structure = structure.tree.children|selectattr("name", "equalto", "src")|first %}
Main project structure:
{% for item in src_structure.children %}
{% if item.type == 'directory' %}
- **{{ item.name }}/**{% if item.name.lower() == 'core' %} - main business logic{% 
elif item.name.lower() == 'models' or item.name.lower() == 'model' %} - data models{% 
elif item.name.lower() == 'services' %} - services for working with external systems{% 
elif item.name.lower() == 'utils' or item.name.lower() == 'helpers' %} - utility functions and helpers{% 
elif item.name.lower() == 'config' %} - project configuration{% 
elif item.name.lower() == 'controllers' %} - request handlers and controllers{% 
elif item.name.lower() == 'views' %} - view components{% 
elif item.name.lower() == 'ui' %} - user interface components{% 
elif item.name.lower() == 'api' %} - API endpoints{% 
elif item.name.lower() == 'db' or item.name.lower() == 'database' %} - database interaction{% 
elif item.name.lower() == 'tests' %} - project tests{% 
else %} - project component{% endif %}

{% endif %}
{% endfor %}
{% else %}
Key project components:
{% for item in structure.tree.children %}
{% if item.type == 'directory' and not item.name.startswith('.') and item.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
- **{{ item.name }}/**{% if item.name.lower() == 'src' %} - source code{% 
elif item.name.lower() == 'tests' or item.name.lower() == 'test' %} - test suite{% 
elif item.name.lower() == 'docs' %} - documentation{% 
elif item.name.lower() == 'config' %} - configuration files{% 
elif item.name.lower() == 'scripts' %} - utility scripts{% 
elif item.name.lower() == 'utils' or item.name.lower() == 'helpers' %} - utility functions{% 
elif item.name.lower() == 'data' %} - data access layer{% 
elif item.name.lower() == 'domain' %} - domain layer with business logic{% 
elif item.name.lower() == 'presentation' or item.name.lower() == 'ui' %} - presentation layer{% 
elif item.name.lower() == 'resources' %} - resource files{% endif %}

{% endif %}
{% endfor %}
{% endif %}

{% endif %}

{% if "installation" in sections %}
## Installation

### Prerequisites

{% if "C#" in technologies|map(attribute="name") or ".NET" in technologies|map(attribute="name") %}
- .NET SDK (recommended version 6.0 or later)
- Visual Studio or Visual Studio Code
{% elif "Java" in technologies|map(attribute="name") %}
- JDK (recommended version 11 or later)
- Maven or Gradle build tools
{% elif "Kotlin" in technologies|map(attribute="name") %}
- JDK (recommended version 11 or later)
- Kotlin compiler
- Maven or Gradle build tools
{% elif "Python" in technologies|map(attribute="name") %}
- Python (recommended version 3.8 or later)
- pip (package manager)
{% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
- Node.js (recommended version 14 or later)
- npm or yarn package manager
{% elif "Rust" in technologies|map(attribute="name") %}
- Rust and Cargo (recommended version 1.56 or later)
{% elif "Go" in technologies|map(attribute="name") %}
- Go (recommended version 1.16 or later)
{% else %}
{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
- {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('name') }}{% if technologies|selectattr('category', 'equalto', 'language')|list|first|attr('version') %} {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('version') }}{% endif %}
{% endif %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'database')|list|length > 0 %}
- {{ technologies|selectattr('category', 'equalto', 'database')|list|first|attr('name') }}
{% endif %}

### Setup

1. Clone the repository:
   ```bash
   git clone {% if metadata.repository_url %}{{ metadata.repository_url }}{% else %}[repository-url]{% endif %}
   
   cd {{ name }}   ```

2. Install dependencies:
   {% if "Python" in technologies|map(attribute="name") %}
   ```bash
   pip install -r requirements.txt
   ```
   {% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
   ```bash
   npm install
   # or
   yarn install
   ```
   {% elif "Rust" in technologies|map(attribute="name") %}
   ```bash
   cargo build
   ```
   {% elif "Go" in technologies|map(attribute="name") %}
   ```bash
   go mod download
   ```
   {% elif "C#" in technologies|map(attribute="name") or ".NET" in technologies|map(attribute="name") %}
   ```bash
   dotnet restore
   dotnet build
   ```
   {% elif "Java" in technologies|map(attribute="name") %}
   ```bash
   # Using Maven
   mvn clean install
   
   # Or using Gradle
   ./gradlew build
   ```
   {% elif "Kotlin" in technologies|map(attribute="name") %}
   ```bash
   # Using Maven
   mvn clean install
   
   # Or using Gradle
   ./gradlew build
   ```
   {% else %}
   ```bash
   # Install dependencies according to your project's requirements
   ```
   {% endif %}

{% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 or structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 or structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
3. Configure the application:
   {% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 %}
   ```bash
   cp config.example.json config.json
   # Edit config.json to match your environment
   ```
   {% elif structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 %}
   ```bash
   cp .env.example .env
   # Edit .env to match your environment
   ```
   {% elif structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
   ```bash
   # Edit appsettings.json to match your environment
   ```
   {% endif %}
{% endif %}

{% endif %}

{% if "configuration" in sections %}
## Configuration

{% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 %}
The project is configured through the `config.json` file.

Main parameters:
- Connection settings
- Operation parameters
- File paths and storage locations
{% elif structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 %}
The project is configured through the `.env` file.

Main environment variables:
- Connection settings
- Operation parameters
- File paths and storage locations
{% elif structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
The project is configured through the `appsettings.json` file.

Main settings:
- Connection strings
- Application settings
- Logging configuration
{% else %}
The project can be configured through the configuration files according to the platform conventions.
{% endif %}

{% endif %}

{% if "project_structure" in sections and structure %}
## Project Structure

```
{{ name }}/
{% for item in structure.tree.children recursive %}
{% if item.type == 'directory' and not item.name.startswith('.') and item.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
├── {{ item.name }}/
{% for child in item.children %}
{% if child.type == 'directory' and not child.name.startswith('.') and child.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
    ├── {{ child.name }}/
{% for grandchild in child.children %}
{% if grandchild.type == 'directory' and not grandchild.name.startswith('.') and grandchild.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
        ├── {{ grandchild.name }}/
{% for greatgrandchild in grandchild.children %}
{% if greatgrandchild.type == 'file' and not greatgrandchild.name.startswith('.') and greatgrandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not greatgrandchild.name.endswith('.pdb') and not greatgrandchild.name.endswith('.dll') and not greatgrandchild.name.endswith('.cache') %}
            ├── {{ greatgrandchild.name }}
{% endif %}
{% endfor %}
{% elif grandchild.type == 'file' and not grandchild.name.startswith('.') and grandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not grandchild.name.endswith('.pdb') and not grandchild.name.endswith('.dll') and not grandchild.name.endswith('.cache') %}
        ├── {{ grandchild.name }}
{% endif %}
{% endfor %}
{% elif child.type == 'file' and not child.name.startswith('.') and child.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not child.name.endswith('.pdb') and not child.name.endswith('.dll') and not child.name.endswith('.cache') %}
    ├── {{ child.name }}
{% endif %}
{% endfor %}
{% elif item.type == 'file' and not item.name.startswith('.') and item.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not item.name.endswith('.pdb') and not item.name.endswith('.dll') and not item.name.endswith('.cache') %}
├── {{ item.name }}
{% endif %}
{% endfor %}
```

{% endif %}

{% if "usage" in sections %}
## Usage

{% if "C#" in technologies|map(attribute="name") or ".NET" in technologies|map(attribute="name") %}
### Running the application

```bash
dotnet run
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```csharp
// Example code for {{ features[0].name|lower }}
```
{% endif %}

{% elif "Python" in technologies|map(attribute="name") %}
### Running the application

```bash
python main.py
# or
python -m {{ name }}
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```python
# Example code for {{ features[0].name|lower }}
```
{% endif %}

{% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
### Running the application

```bash
npm start
# or
node index.js
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```javascript
// Example code for {{ features[0].name|lower }}
```
{% endif %}

{% elif "Java" in technologies|map(attribute="name") or "Kotlin" in technologies|map(attribute="name") %}
### Running the application

```bash
# Using Maven
mvn exec:java -Dexec.mainClass="com.example.MainClass"

# Or using Gradle
./gradlew run
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```java
// Example code for {{ features[0].name|lower }}
```
{% endif %}

{% elif "Rust" in technologies|map(attribute="name") %}
### Running the application

```bash
cargo run
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```rust
// Example code for {{ features[0].name|lower }}
```
{% endif %}

{% elif "Go" in technologies|map(attribute="name") %}
### Running the application

```bash
go run main.go
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```go
// Example code for {{ features[0].name|lower }}
```
{% endif %}

{% else %}
### Running the application

```bash
# Run the application according to the project's requirements
```

{% if features|length > 0 and features[0].name is defined %}
### {{ features[0].name }}

```
// Example usage for {{ features[0].name|lower }}
```
{% endif %}
{% endif %}

{% endif %}

{% if "optimization" in sections %}
## Optimization

{% if features|selectattr("category", "equalto", "file_processing")|list|length > 0 %}
- File processing optimization
- Data caching for faster access
{% elif features|selectattr("category", "equalto", "database")|list|length > 0 %}
- Database query optimization
- Index usage for faster lookups
{% else %}
- Performance optimization
- Efficient resource utilization
{% endif %}

{% endif %}

{% if "contributing" in sections %}
## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add new feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

{% endif %}

{% if "license" in sections %}
## License

{% if metadata.license_type %}
This project is licensed under the {{ metadata.license_type }} License
{% else %}
This project is licensed under the license specified in the [LICENSE](LICENSE) file in the repository.
{% endif %}
{% endif %} 
"""
        
        self.file_repository.save_file(base_path, content)
    
    def _create_minimal_template(self) -> None:
        """Creates a minimal template."""
        minimal_dir = os.path.join(self.templates_dir, "minimal")
        os.makedirs(minimal_dir, exist_ok=True)
        
        base_path = os.path.join(minimal_dir, "base.md.j2")
        
        content = """# {{ name }}

{% if "overview" in sections %}
## Overview

{{ description }}

{% if name is defined and '_' in name or '-' in name %}
**{{ name|replace('_', ' ')|replace('-', ' ')|title }}** - {% endif %}{% if features|length > 0 %}a tool for {{ features[0].description|lower }}{% if features|length > 1 %} and {{ features[1].description|lower }}{% endif %}.
{% else %}
{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
This project is built with {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('name') }}.
{% endif %}
{% endif %}

{% if metadata.has_documentation %}
Documentation is available in the project directory.
{% endif %}
{% endif %}

{% if "technologies" in sections %}
## Technologies

{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
### Programming Languages
{% for tech in technologies|selectattr('category', 'equalto', 'language')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'framework')|list|length > 0 %}
### Frameworks
{% for tech in technologies|selectattr('category', 'equalto', 'framework')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'frontend')|list|length > 0 or technologies|selectattr('category', 'equalto', 'backend')|list|length > 0 %}
### Front-end / Back-end
{% for tech in technologies|selectattr('category', 'equalto', 'frontend')|list %}
- **{{ tech.name }}** (Front-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% for tech in technologies|selectattr('category', 'equalto', 'backend')|list %}
- **{{ tech.name }}** (Back-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'database')|list|length > 0 %}
### Database
{% for tech in technologies|selectattr('category', 'equalto', 'database')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'devops')|list|length > 0 %}
### DevOps
{% for tech in technologies|selectattr('category', 'equalto', 'devops')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'testing')|list|length > 0 %}
### Testing
{% for tech in technologies|selectattr('category', 'equalto', 'testing')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'architecture')|list|length > 0 %}
### Architecture Patterns
{% for tech in technologies|selectattr('category', 'equalto', 'architecture')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'other')|list|length > 0 %}
### Other
{% for tech in technologies|selectattr('category', 'equalto', 'other')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}
{% endif %}

{% if "project_structure" in sections and structure %}
## Project Structure

```
{{ name }}/
{% for item in structure.tree.children recursive %}
{% if item.type == 'directory' and not item.name.startswith('.') and item.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
├── {{ item.name }}/
{% for child in item.children %}
{% if child.type == 'directory' and not child.name.startswith('.') and child.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
    ├── {{ child.name }}/
{% for grandchild in child.children %}
{% if grandchild.type == 'directory' and not grandchild.name.startswith('.') and grandchild.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
        ├── {{ grandchild.name }}/
{% for greatgrandchild in grandchild.children %}
{% if greatgrandchild.type == 'file' and not greatgrandchild.name.startswith('.') and greatgrandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not greatgrandchild.name.endswith('.pdb') and not greatgrandchild.name.endswith('.dll') and not greatgrandchild.name.endswith('.cache') %}
            ├── {{ greatgrandchild.name }}
{% endif %}
{% endfor %}
{% elif grandchild.type == 'file' and not grandchild.name.startswith('.') and grandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not grandchild.name.endswith('.pdb') and not grandchild.name.endswith('.dll') and not grandchild.name.endswith('.cache') %}
        ├── {{ grandchild.name }}
{% endif %}
{% endfor %}
{% elif child.type == 'file' and not child.name.startswith('.') and child.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not child.name.endswith('.pdb') and not child.name.endswith('.dll') and not child.name.endswith('.cache') %}
    ├── {{ child.name }}
{% endif %}
{% endfor %}
{% elif item.type == 'file' and not item.name.startswith('.') and item.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not item.name.endswith('.pdb') and not item.name.endswith('.dll') and not item.name.endswith('.cache') %}
├── {{ item.name }}
{% endif %}
{% endfor %}
```

{% endif %}

{% if "installation" in sections %}
## Installation

1. Clone the repository: `git clone {% if metadata.repository_url %}{{ metadata.repository_url }}{% else %}[repository-url]{% endif %}`
2. Navigate to the project directory: `cd {{ name }}`
3. Install dependencies and build the project.
{% endif %}

{% if "usage" in sections %}
## Usage

Run the application using the instructions relevant to your project type.
{% endif %}
"""
        
        self.file_repository.save_file(base_path, content)
    
    def _create_detailed_template(self) -> None:
        """Creates a detailed template."""
        detailed_dir = os.path.join(self.templates_dir, "detailed")
        os.makedirs(detailed_dir, exist_ok=True)
        
        base_path = os.path.join(detailed_dir, "base.md.j2")
        
        content = """# {{ name }}

## Table of Contents

{% for section in sections %}
{% if section != "table_of_contents" %}
- [{{ section|title|replace("_", " ") }}](#{{ section|lower|replace("_", "-") }})
{% endif %}
{% endfor %}

{% if "overview" in sections %}
## Overview

{{ description }}

{% if name is defined and '_' in name or '-' in name %}
**{{ name|replace('_', ' ')|replace('-', ' ')|title }}** - {% endif %}{% if features|length > 0 %}a tool for {{ features[0].description|lower }}{% if features|length > 1 %} and {{ features[1].description|lower }}{% endif %}.
{% else %}
{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
This project is built with {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('name') }}.
{% endif %}
{% endif %}

{% if metadata.has_documentation %}
Documentation is available in the project directory.
{% endif %}

### Target Audience

*Describe the target audience here*

### Key Features

{% if features|length > 0 %}
{% for feature in features %}
- {{ feature.name }}: {{ feature.description }}
{% endfor %}
{% else %}
*List key features here*
{% endif %}

{% endif %}

{% if "features" in sections and features %}
## Features

{% for feature in features %}
### {{ feature.name }}

{{ feature.description }}

{% endfor %}
{% endif %}

{% if "technologies" in sections %}
## Technologies

{% if technologies %}
### Development

{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
#### Programming Languages
{% for tech in technologies|selectattr('category', 'equalto', 'language')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'framework')|list|length > 0 %}
#### Frameworks
{% for tech in technologies|selectattr('category', 'equalto', 'framework')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'frontend')|list|length > 0 or technologies|selectattr('category', 'equalto', 'backend')|list|length > 0 %}
#### Front-end / Back-end
{% for tech in technologies|selectattr('category', 'equalto', 'frontend')|list %}
- **{{ tech.name }}** (Front-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% for tech in technologies|selectattr('category', 'equalto', 'backend')|list %}
- **{{ tech.name }}** (Back-end){% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'other')|list|length > 0 %}
#### Other
{% for tech in technologies|selectattr('category', 'equalto', 'other')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

### Infrastructure

{% if technologies|selectattr('category', 'equalto', 'database')|list|length > 0 %}
#### Database
{% for tech in technologies|selectattr('category', 'equalto', 'database')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'devops')|list|length > 0 %}
#### DevOps
{% for tech in technologies|selectattr('category', 'equalto', 'devops')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

### Testing

{% if technologies|selectattr('category', 'equalto', 'testing')|list|length > 0 %}
{% for tech in technologies|selectattr('category', 'equalto', 'testing')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}
{% else %}
*List technologies here*
{% endif %}

{% endif %}

{% if "architecture" in sections %}
## Architecture

{% if metadata.architecture_description is defined %}
{{ metadata.architecture_description }}
{% else %}
*Describe the architecture of the project here*
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'architecture')|list|length > 0 %}
### Architecture Patterns
{% for tech in technologies|selectattr('category', 'equalto', 'architecture')|list %}
- **{{ tech.name }}**{% if tech.version %} ({{ tech.version }}){% endif %}

{% endfor %}
{% endif %}

{% if structure.tree.children|selectattr("name", "equalto", "src")|list|length > 0 %}
{% set src_structure = structure.tree.children|selectattr("name", "equalto", "src")|first %}
### Main Project Components
{% for item in src_structure.children %}
{% if item.type == 'directory' %}
- **{{ item.name }}/**{% if item.name.lower() == 'core' %} - main business logic{% 
elif item.name.lower() == 'models' or item.name.lower() == 'model' %} - data models{% 
elif item.name.lower() == 'services' %} - services for working with external systems{% 
elif item.name.lower() == 'utils' or item.name.lower() == 'helpers' %} - utility functions and helpers{% 
elif item.name.lower() == 'config' %} - project configuration{% 
elif item.name.lower() == 'controllers' %} - request handlers and controllers{% 
elif item.name.lower() == 'views' %} - view components{% 
elif item.name.lower() == 'ui' %} - user interface components{% 
elif item.name.lower() == 'api' %} - API endpoints{% 
elif item.name.lower() == 'db' or item.name.lower() == 'database' %} - database interaction{% 
elif item.name.lower() == 'tests' %} - project tests{% 
else %} - project component{% endif %}

{% endif %}
{% endfor %}
{% endif %}

{% endif %}

{% if "installation" in sections %}
## Installation

### Prerequisites

{% if "C#" in technologies|map(attribute="name") or ".NET" in technologies|map(attribute="name") %}
- .NET SDK (recommended version 6.0 or later)
- Visual Studio or Visual Studio Code
{% elif "Java" in technologies|map(attribute="name") %}
- JDK (recommended version 11 or later)
- Maven or Gradle build tools
{% elif "Kotlin" in technologies|map(attribute="name") %}
- JDK (recommended version 11 or later)
- Kotlin compiler
- Maven or Gradle build tools
{% elif "Python" in technologies|map(attribute="name") %}
- Python (recommended version 3.8 or later)
- pip (package manager)
{% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
- Node.js (recommended version 14 or later)
- npm or yarn package manager
{% elif "Rust" in technologies|map(attribute="name") %}
- Rust and Cargo (recommended version 1.56 or later)
{% elif "Go" in technologies|map(attribute="name") %}
- Go (recommended version 1.16 or later)
{% else %}
{% if technologies|selectattr('category', 'equalto', 'language')|list|length > 0 %}
- {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('name') }}{% if technologies|selectattr('category', 'equalto', 'language')|list|first|attr('version') %} {{ technologies|selectattr('category', 'equalto', 'language')|list|first|attr('version') }}{% endif %}
{% endif %}
{% endif %}

{% if technologies|selectattr('category', 'equalto', 'database')|list|length > 0 %}
- {{ technologies|selectattr('category', 'equalto', 'database')|list|first|attr('name') }}
{% endif %}

### Setup

1. Clone the repository:
   ```bash
   git clone {% if metadata.repository_url %}{{ metadata.repository_url }}{% else %}[repository-url]{% endif %}
   cd {{ name }}
   ```

2. Install dependencies:
   {% if "Python" in technologies|map(attribute="name") %}
   ```bash
   pip install -r requirements.txt
   ```
   {% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
   ```bash
   npm install
   # or
   yarn install
   ```
   {% elif "Rust" in technologies|map(attribute="name") %}
   ```bash
   cargo build
   ```
   {% elif "Go" in technologies|map(attribute="name") %}
   ```bash
   go mod download
   ```
   {% elif "C#" in technologies|map(attribute="name") or ".NET" in technologies|map(attribute="name") %}
   ```bash
   dotnet restore
   dotnet build
   ```
   {% elif "Java" in technologies|map(attribute="name") %}
   ```bash
   # Using Maven
   mvn clean install
   
   # Or using Gradle
   ./gradlew build
   ```
   {% elif "Kotlin" in technologies|map(attribute="name") %}
   ```bash
   # Using Maven
   mvn clean install
   
   # Or using Gradle
   ./gradlew build
   ```
   {% else %}
   ```bash
   # Install dependencies according to your project's requirements
   ```
   {% endif %}

{% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 or structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 or structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
3. Configure the application:
   {% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 %}
   ```bash
   cp config.example.json config.json
   # Edit config.json to match your environment
   ```
   {% elif structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 %}
   ```bash
   cp .env.example .env
   # Edit .env to match your environment
   ```
   {% elif structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
   ```bash
   # Edit appsettings.json to match your environment
   ```
   {% endif %}
{% endif %}

{% endif %}

{% if "configuration" in sections %}
## Configuration

{% if structure.tree.children|selectattr("name", "equalto", "config.json")|list|length > 0 %}
The project is configured through the `config.json` file.

### Configuration Parameters

- Connection settings
- Operation parameters
- File paths and storage locations
{% elif structure.tree.children|selectattr("name", "equalto", ".env")|list|length > 0 %}
The project is configured through the `.env` file.

### Environment Variables

- Connection settings
- Operation parameters
- File paths and storage locations
{% elif structure.tree.children|selectattr("name", "equalto", "appsettings.json")|list|length > 0 %}
The project is configured through the `appsettings.json` file.

### Configuration Parameters

- Connection strings
- Application settings
- Logging configuration
{% else %}
The project can be configured through the configuration files according to the platform conventions.

### Configuration Parameters

*Describe configuration parameters here*

### Environment Variables

*List environment variables here*
{% endif %}

{% endif %}

{% if "project_structure" in sections and structure %}
## Project Structure

```
{{ name }}/
{% for item in structure.tree.children recursive %}
{% if item.type == 'directory' and not item.name.startswith('.') and item.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
├── {{ item.name }}/
{% for child in item.children %}
{% if child.type == 'directory' and not child.name.startswith('.') and child.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
    ├── {{ child.name }}/
{% for grandchild in child.children %}
{% if grandchild.type == 'directory' and not grandchild.name.startswith('.') and grandchild.name.lower() not in ['node_modules', '__pycache__', 'venv', 'env', 'bin', 'obj', '.vs', '.vscode', '.idea', 'dist', 'build', 'target'] %}
        ├── {{ grandchild.name }}/
{% for greatgrandchild in grandchild.children %}
{% if greatgrandchild.type == 'file' and not greatgrandchild.name.startswith('.') and greatgrandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not greatgrandchild.name.endswith('.pdb') and not greatgrandchild.name.endswith('.dll') and not greatgrandchild.name.endswith('.cache') %}
            ├── {{ greatgrandchild.name }}
{% endif %}
{% endfor %}
{% elif grandchild.type == 'file' and not grandchild.name.startswith('.') and grandchild.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not grandchild.name.endswith('.pdb') and not grandchild.name.endswith('.dll') and not grandchild.name.endswith('.cache') %}
        ├── {{ grandchild.name }}
{% endif %}
{% endfor %}
{% elif child.type == 'file' and not child.name.startswith('.') and child.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not child.name.endswith('.pdb') and not child.name.endswith('.dll') and not child.name.endswith('.cache') %}
    ├── {{ child.name }}
{% endif %}
{% endfor %}
{% elif item.type == 'file' and not item.name.startswith('.') and item.name not in ['__init__.py', 'Thumbs.db', '.DS_Store'] and not item.name.endswith('.pdb') and not item.name.endswith('.dll') and not item.name.endswith('.cache') %}
├── {{ item.name }}
{% endif %}
{% endfor %}
```

### Key Components

{% if structure.tree.children|selectattr("name", "equalto", "src")|list|length > 0 %}
{% set src_structure = structure.tree.children|selectattr("name", "equalto", "src")|first %}
{% for item in src_structure.children %}
{% if item.type == 'directory' %}
- **{{ item.name }}/**{% if item.name.lower() == 'core' %} - Core business logic{% 
elif item.name.lower() == 'models' or item.name.lower() == 'model' %} - Data models and entities{% 
elif item.name.lower() == 'services' %} - Services for working with external systems{% 
elif item.name.lower() == 'utils' or item.name.lower() == 'helpers' %} - Utility functions and helpers{% 
elif item.name.lower() == 'config' %} - Project configuration{% 
elif item.name.lower() == 'controllers' %} - Request handlers and controllers{% 
elif item.name.lower() == 'views' %} - View components{% 
elif item.name.lower() == 'ui' %} - User interface components{% 
elif item.name.lower() == 'api' %} - API endpoints{% 
elif item.name.lower() == 'db' or item.name.lower() == 'database' %} - Database interaction{% 
elif item.name.lower() == 'tests' %} - Project tests{% 
else %} - Project component{% endif %}

{% endif %}
{% endfor %}
{% else %}
*Describe key components here*
{% endif %}

{% endif %}

{% if "api_documentation" in sections %}
## API Documentation

{% if "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resource` | GET | Retrieve resources |
| `/api/resource/:id` | GET | Retrieve a specific resource |
| `/api/resource` | POST | Create a new resource |
| `/api/resource/:id` | PUT | Update a specific resource |
| `/api/resource/:id` | DELETE | Delete a specific resource |

### Request and Response Examples

#### Get Resources

```
GET /api/resource
```

Response:
```json
[
  {
    "id": 1,
    "name": "Resource Name",
    "description": "Resource description"
  }
]
```
{% else %}
*Document API endpoints here*
{% endif %}

{% endif %}

{% if "testing" in sections %}
## Testing

{% if "Python" in technologies|map(attribute="name") %}
### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov=src
```
{% elif "Node.js" in technologies|map(attribute="name") or "JavaScript" in technologies|map(attribute="name") %}
### Running Tests

```bash
npm test
```

### Test Coverage

```bash
npm run test:coverage
```
{% else %}
*Describe testing approach and how to run tests*
{% endif %}

{% endif %}

{% if "deployment" in sections %}
## Deployment

{% if "Docker" in technologies|map(attribute="name") %}
### Docker Deployment

```bash
docker build -t {{ name|lower }} .
docker run -p 8080:8080 {{ name|lower }}
```
{% else %}
*Describe deployment process and environments*
{% endif %}

{% endif %}

{% if "optimization" in sections %}
## Optimization

*Describe optimization strategies and performance considerations*

{% endif %}

{% if "roadmap" in sections %}
## Roadmap

*List planned features and improvements*

{% endif %}

{% if "contributing" in sections %}
## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Submit a Pull Request

Please make sure your code follows the project's coding standards and includes appropriate tests.

{% endif %}

{% if "license" in sections %}
## License

{% if metadata.license_type %}
This project is licensed under the {{ metadata.license_type }} License - see the LICENSE file for details.
{% else %}
This project is licensed under the [LICENSE](LICENSE) file in the repository.
{% endif %}
{% endif %}

{% if "acknowledgements" in sections %}
## Acknowledgements

*List acknowledgements here*

{% endif %}
"""
        
        self.file_repository.save_file(base_path, content)