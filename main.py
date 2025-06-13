#!/usr/bin/env python
"""
ReadmeForge - Tool for generating README.md based on project analysis.

This script is the entry point for the application. It initializes all necessary components,
including repositories, analyzers, template renderer, and CLI interface.
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.domain.usecases.generate_readme import ReadmeGeneratorUseCase
from src.infrastructure.repositories.file_repository import FileRepository
from src.infrastructure.repositories.config_repository import ConfigRepository
from src.infrastructure.analyzers.project_analyzer import ProjectAnalyzer
from src.infrastructure.analyzers.technology_analyzer import TechnologyAnalyzer
from src.infrastructure.analyzers.structure_analyzer import StructureAnalyzer
from src.infrastructure.templates.template_renderer import TemplateRenderer
from src.interfaces.cli.commands import CLIHandler, setup_cli_commands, cli


def main():
    """Main application function."""
    base_dir = Path(__file__).resolve().parent
    config_path = os.path.join(base_dir, "config.json")
    templates_dir = os.path.join(base_dir, "src", "infrastructure", "templates")
    
    file_repository = FileRepository()
    config_repository = ConfigRepository(config_path, file_repository)
    
    technology_analyzer = TechnologyAnalyzer(file_repository, config_repository)
    structure_analyzer = StructureAnalyzer(file_repository, config_repository)
    project_analyzer = ProjectAnalyzer(technology_analyzer, structure_analyzer, file_repository)
    
    template_renderer = TemplateRenderer(templates_dir, file_repository, config_repository)
    
    readme_generator = ReadmeGeneratorUseCase(project_analyzer, template_renderer, file_repository)
    
    cli_handler = CLIHandler(readme_generator)
    setup_cli_commands(cli_handler)
    
    return cli


if __name__ == "__main__":
    cli_app = main()
    cli_app()
