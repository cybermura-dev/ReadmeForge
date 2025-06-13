"""Abstract ports for working with templates."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class TemplateRendererPort(ABC):
    """Abstract port for rendering templates."""
    
    @abstractmethod
    def render(self, 
               template_name: str, 
               context: Dict[str, Any],
               sections: Optional[List[str]] = None) -> str:
        """
        Renders a template with the given context.
        
        Args:
            template_name: The name of the template.
            context: The data context to substitute into the template.
            sections: A list of sections to include (if None, all sections are used).
        
        Returns:
            str: The rendered template.
        """
        pass
    
    @abstractmethod
    def get_available_templates(self) -> List[str]:
        """
        Returns a list of available templates.
        
        Returns:
            List[str]: A list of available template names.
        """
        pass
    
    @abstractmethod
    def get_sections_for_template(self, template_name: str) -> List[str]:
        """
        Returns a list of sections for the specified template.
        
        Args:
            template_name: The name of the template.
            
        Returns:
            List[str]: A list of section names.
        """
        pass 