"""Use case for generating a README.md file."""
from typing import List, Dict, Any, Optional

from ..entities.project import Project


class ReadmeGeneratorUseCase:
    """Use case for generating a README file."""
    
    def __init__(self, project_analyzer, template_renderer, file_repository):
        """
        Initializes the use case.
        
        Args:
            project_analyzer: The project analyzer.
            template_renderer: The template renderer.
            file_repository: The repository for working with the file system.
        """
        self.project_analyzer = project_analyzer
        self.template_renderer = template_renderer
        self.file_repository = file_repository
    
    def execute(self, 
                project_path: str, 
                output_path: Optional[str] = None,
                template_name: str = "standard",
                section_names: Optional[List[str]] = None) -> str:
        """
        Executes the README generation scenario.
        
        Args:
            project_path: The path to the project to be analyzed.
            output_path: The path to save the README file (defaults to the project root).
            template_name: The name of the template to generate the README.
            section_names: A list of sections to include in the README.
            
        Returns:
            str: The path to the generated README file.
        """
        project = self.project_analyzer.analyze(project_path)
        
        if not output_path:
            output_path = self.file_repository.join_path(project_path, "README.md")
        
        readme_content = self.template_renderer.render(
            template_name=template_name,
            context=project.to_dict(),
            sections=section_names
        )
        
        self.file_repository.save_file(output_path, readme_content)
        
        return output_path 