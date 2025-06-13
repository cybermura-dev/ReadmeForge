"""Module with project entities."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Technology:
    """Technology used in the project."""
    name: str
    category: str
    version: Optional[str] = None
    importance: int = 1


@dataclass
class Feature:
    """Project feature."""
    name: str
    description: str
    category: str
    priority: int = 3


@dataclass
class Project:
    """Project to be analyzed."""
    name: str
    path: str
    description: str = ""
    technologies: List[Technology] = field(default_factory=list)
    features: List[Feature] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_feature_descriptions(self) -> Dict[str, str]:
        """
        Returns a dictionary with descriptions of the project's features.
        
        Returns:
            Dict[str, str]: A dictionary with feature names and their descriptions.
        """
        return {feature.name: feature.description for feature in self.features}
    
    def get_technologies_by_category(self) -> Dict[str, List[Technology]]:
        """
        Groups technologies by category.
        
        Returns:
            Dict[str, List[Technology]]: A dictionary with categories and lists of technologies.
        """
        result = {}
        for tech in self.technologies:
            if tech.category not in result:
                result[tech.category] = []
            result[tech.category].append(tech)
        return result
    
    def get_primary_language(self) -> Optional[str]:
        """
        Returns the primary programming language of the project.
        
        Returns:
            Optional[str]: The name of the primary programming language or None.
        """
        languages = [tech for tech in self.technologies if tech.category == "language"]
        if languages:
            languages.sort(key=lambda x: x.importance, reverse=True)
            return languages[0].name
        return None
    
    def get_primary_framework(self) -> Optional[str]:
        """
        Returns the primary framework of the project.
        
        Returns:
            Optional[str]: The name of the primary framework or None.
        """
        frameworks = [tech for tech in self.technologies if tech.category == "framework"]
        if frameworks:
            frameworks.sort(key=lambda x: x.importance, reverse=True)
            return frameworks[0].name
        return None
    
    @property
    def main_language(self) -> Optional[str]:
        """Determines the main language of the project from the list of technologies."""
        if not self.technologies:
            return None
        
        sorted_tech = sorted(
            self.technologies, 
            key=lambda t: t.importance, 
            reverse=True
        )
        
        programming_languages = [t for t in sorted_tech if t.category == "language"]
        if programming_languages:
            return programming_languages[0].name
        
        return sorted_tech[0].name if sorted_tech else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the project to a dictionary for further processing by the templating engine."""
        return {
            "name": self.name,
            "description": self.description,
            "technologies": self.technologies,
            "features": self.features,
            "structure": self.structure,
            "metadata": self.metadata,
            "main_language": self.main_language
        } 