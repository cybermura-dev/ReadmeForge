"""Module with CLI commands for ReadmeForge."""
import os
import click
from typing import Optional, List

from ...domain.usecases.generate_readme import ReadmeGeneratorUseCase


class CLIHandler:
    """CLI commands handler."""
    
    def __init__(self, readme_generator: ReadmeGeneratorUseCase):
        """
        Initialization of the CLI handler.
        
        Args:
            readme_generator: Use case for generating README
        """
        self.readme_generator = readme_generator
    
    def generate(self, 
                 project_path: str, 
                 output_path: Optional[str] = None,
                 template_name: str = "standard",
                 sections: Optional[List[str]] = None) -> None:
        """
        Generates a README.md file for the specified project.
        
        Args:
            project_path: The path to the project
            output_path: The path to save the README (default - project root)
            template_name: The name of the template for generation
            sections: A list of sections to include
        """
        if not os.path.isabs(project_path):
            project_path = os.path.abspath(project_path)
        
        result_path = self.readme_generator.execute(
            project_path=project_path,
            output_path=output_path,
            template_name=template_name,
            section_names=sections
        )
        
        click.echo(f"README.md successfully generated: {result_path}")


@click.group()
def cli():
    """Utility for generating README.md files based on project structure."""
    pass


def setup_cli_commands(cli_handler: CLIHandler) -> None:
    """
    Sets up CLI commands.
    
    Args:
        cli_handler: CLI commands handler
    """
    
    @cli.command("generate")
    @click.argument("project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
    @click.option(
        "--output", "-o",
        help="The path to save the README.md file",
        type=click.Path(dir_okay=False)
    )
    @click.option(
        "--template", "-t",
        help="The name of the template (standard, minimal, detailed)",
        type=click.Choice(["standard", "minimal", "detailed"]),
        default="standard"
    )
    @click.option(
        "--section", "-s",
        help="The section to include (can be specified multiple times)",
        type=str,
        multiple=True
    )
    def generate_readme(project_path: str, output: Optional[str], template: str, section: List[str]) -> None:
        """Generates a README.md file for the specified project."""
        sections = list(section) if section else None
        cli_handler.generate(
            project_path=project_path,
            output_path=output,
            template_name=template,
            sections=sections
        ) 