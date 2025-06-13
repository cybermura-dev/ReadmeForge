"""Structure analyzer for the project."""
import os
from typing import Dict, Any, List

from ...domain.ports.analyzers import StructureAnalyzerPort
from ...domain.ports.repositories import FileRepositoryPort, ConfigRepositoryPort


class StructureAnalyzer(StructureAnalyzerPort):
    """Structure analyzer for the project."""
    
    def __init__(self, file_repository: FileRepositoryPort, config_repository: ConfigRepositoryPort):
        """
        Initializes the structure analyzer.
        
        Args:
            file_repository: The repository for working with files
            config_repository: The repository for working with configuration
        """
        self.file_repository = file_repository
        self.config_repository = config_repository
    
    def analyze_structure(self, project_path: str) -> Dict[str, Any]:
        """
        Analyzes the structure of the project and returns information about it.
        
        Args:
            project_path: The path to the project root
        
        Returns:
            Dict[str, Any]: Information about the project structure
        """
        ignored_dirs = [
            '.git', '.github', '.vscode', '.idea', '.vs', 
            'node_modules', '__pycache__', 'venv', 'env',
            'dist', 'build', 'target', 'bin', 'obj', 
            '.pytest_cache', '.coverage', '.next', 'coverage',
            '.nuget', 'packages', '.gradle'
        ]
        
        ignored_files = [
            '.gitignore', '.gitattributes', '.DS_Store', 'Thumbs.db',
            '.env', '.env.local', '.env.development', '.env.test', '.env.production',
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.obj', '*.o',
            '*.a', '*.lib', '*.egg', '*.egg-info', '*.whl', '*.pdb', '*.cache',
            '*.class', '*.jar', '*.war', '*.ear', '*.zip', '*.tar.gz', '*.rar'
        ]
        
        tree = self._build_tree(project_path, project_path, ignored_dirs, ignored_files)
        
        file_stats = self._collect_file_stats(project_path, ignored_dirs, ignored_files)
        
        return {
            "tree": tree,
            "stats": file_stats
        }
    
    def _build_tree(self, base_path: str, path: str, ignored_dirs: List[str], ignored_files: List[str], max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively builds a tree of the project's file structure.
        
        Args:
            base_path: The base path of the project
            path: The current path
            ignored_dirs: The list of ignored directories
            ignored_files: The list of ignored files
            max_depth: The maximum depth of recursion
        
        Returns:
            Dict[str, Any]: The file structure tree
        """
        if max_depth <= 0:
            return {"name": os.path.basename(path), "type": "directory", "children": [{"name": "...", "type": "ellipsis"}]}
        
        result = {
            "name": os.path.basename(path) or os.path.basename(os.path.dirname(path)),
            "type": "directory",
            "children": []
        }
        
        try:
            items = os.listdir(path)
            
            directories = []
            files = []
            
            for item in items:
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    if item in ignored_dirs or any(item.endswith(pattern[1:]) for pattern in ignored_dirs if pattern.startswith('*')):
                        continue
                    directories.append(item)
                else:
                    if item in ignored_files or any(item.endswith(pattern[1:]) for pattern in ignored_files if pattern.startswith('*')):
                        continue
                    files.append(item)
            
            for directory in sorted(directories):
                dir_path = os.path.join(path, directory)
                child = self._build_tree(base_path, dir_path, ignored_dirs, ignored_files, max_depth - 1)
                result["children"].append(child)
            
            for file in sorted(files):
                file_path = os.path.join(path, file)
                result["children"].append({
                    "name": file,
                    "type": "file"
                })
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def _collect_file_stats(self, project_path: str, ignored_dirs: List[str], ignored_files: List[str]) -> Dict[str, Any]:
        """
        Collects statistics on the project's files.
        
        Args:
            project_path: The path to the project root
            ignored_dirs: The list of ignored directories
            ignored_files: The list of ignored files
        
        Returns:
            Dict[str, Any]: Statistics on the files
        """
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "file_types": {},
            "largest_files": []
        }
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not any(d.endswith(pattern[1:]) for pattern in ignored_dirs if pattern.startswith('*'))]
            
            stats["total_dirs"] += len(dirs)
            
            for file in files:
                if file in ignored_files or any(file.endswith(pattern[1:]) for pattern in ignored_files if pattern.startswith('*')):
                    continue
                
                stats["total_files"] += 1
                
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext:
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                
                try:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    if len(stats["largest_files"]) < 5 or file_size > stats["largest_files"][-1]["size"]:
                        stats["largest_files"].append({
                            "path": os.path.relpath(file_path, project_path),
                            "size": file_size
                        })
                        stats["largest_files"] = sorted(stats["largest_files"], key=lambda x: x["size"], reverse=True)[:5]
                except:
                    pass
        
        return stats 