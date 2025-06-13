"""Abstract ports for project analyzers."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from ..entities.project import Project


class ProjectAnalyzerPort(ABC):
    """Abstract port for a project analyzer."""
    
    @abstractmethod
    def analyze(self, project_path: str) -> Project:
        """
        Analyzes the project and returns a Project object.
        
        Args:
            project_path: The path to the project root.
        
        Returns:
            Project: The analyzed project.
        """
        pass


class TechnologyAnalyzerPort(ABC):
    """Abstract port for a project technology analyzer."""
    
    @abstractmethod
    def detect_technologies(self, project_path: str) -> Dict[str, Any]:
        """
        Detects the technologies used in the project.
        
        Args:
            project_path: The path to the project root.
        
        Returns:
            Dict[str, Any]: A dictionary of detected technologies and their metadata.
        """
        pass


class StructureAnalyzerPort(ABC):
    """Abstract port for a project structure analyzer."""
    
    @abstractmethod
    def analyze_structure(self, project_path: str) -> Dict[str, Any]:
        """
        Analyzes the file and directory structure of the project.
        
        Args:
            project_path: The path to the project root.
        
        Returns:
            Dict[str, Any]: Information about the project structure.
        """
        pass 