"""Main project analyzer."""
import os
import re
from typing import Dict, List, Any, Optional

from ...domain.ports.analyzers import ProjectAnalyzerPort, TechnologyAnalyzerPort, StructureAnalyzerPort
from ...domain.ports.repositories import FileRepositoryPort
from ...domain.entities.project import Project, Technology, Feature


class ProjectAnalyzer(ProjectAnalyzerPort):
    """Main project analyzer."""
    
    def __init__(self, 
                 technology_analyzer: TechnologyAnalyzerPort, 
                 structure_analyzer: StructureAnalyzerPort,
                 file_repository: FileRepositoryPort):
        """
        Initializes the project analyzer.
        
        Args:
            technology_analyzer: Technology analyzer
            structure_analyzer: Structure analyzer
            file_repository: File repository
        """
        self.technology_analyzer = technology_analyzer
        self.structure_analyzer = structure_analyzer
        self.file_repository = file_repository
    
    def analyze(self, project_path: str) -> Project:
        """
        Analyzes the project and returns a Project object.
        
        Args:
            project_path: The path to the project root
        
        Returns:
            Project: Analyzed project
        """
        project_name = self._detect_project_name(project_path)
        
        project = Project(
            name=project_name,
            path=project_path,
            description=self._detect_project_description(project_path)
        )
        
        structure_data = self.structure_analyzer.analyze_structure(project_path)
        project.structure = structure_data
        
        tech_data = self.technology_analyzer.detect_technologies(project_path)
        
        tech_data = self._enrich_technologies_from_source(project_path, tech_data)
        
        required_categories = ['language', 'framework', 'frontend', 'backend', 'database', 'devops', 'testing', 'architecture', 'other']
        for category in required_categories:
            if category not in tech_data:
                tech_data[category] = []
        
        project.technologies = self._convert_technologies_data(tech_data)

        project.features = self._detect_project_features(project_path, project.technologies)
        
        project.metadata = {
            "has_tests": self._detect_has_tests(project_path),
            "has_documentation": self._detect_has_documentation(project_path),
            "license_type": self._detect_license_type(project_path),
            "repository_url": self._detect_repository_url(project_path),
            "architecture_description": self._detect_architecture_description(project_path, project.technologies, structure_data)
        }
        
        return project
    
    def _detect_project_name(self, project_path: str) -> str:
        """
        Determines the project name.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            str: Project name
        """
        package_json_path = os.path.join(project_path, "package.json")
        if self.file_repository.file_exists(package_json_path):
            try:
                content = self.file_repository.read_file(package_json_path)
                import json
                package_data = json.loads(content)
                if "name" in package_data:
                    return package_data["name"]
            except:
                pass
        
        setup_py_path = os.path.join(project_path, "setup.py")
        if self.file_repository.file_exists(setup_py_path):
            try:
                content = self.file_repository.read_file(setup_py_path)
                name_match = re.search(r'name=["\']([^"\']+)["\']', content)
                if name_match:
                    return name_match.group(1)
            except:
                pass
        
        cargo_toml_path = os.path.join(project_path, "Cargo.toml")
        if self.file_repository.file_exists(cargo_toml_path):
            try:
                content = self.file_repository.read_file(cargo_toml_path)
                name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if name_match:
                    return name_match.group(1)
            except:
                pass
        
        csproj_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith('.csproj'):
                    csproj_files.append(os.path.join(root, file))
        
        if csproj_files:
            try:
                content = self.file_repository.read_file(csproj_files[0])
                name_match = re.search(r'<AssemblyName>([^<]+)</AssemblyName>', content)
                if name_match:
                    return name_match.group(1)
                
                return os.path.basename(csproj_files[0]).replace('.csproj', '')
            except:
                pass
        
        return os.path.basename(os.path.normpath(project_path))
    
    def _detect_project_description(self, project_path: str) -> str:
        """
        Determines the project description.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            str: Project description
        """
        description = ""
        
        package_json_path = os.path.join(project_path, "package.json")
        if self.file_repository.file_exists(package_json_path):
            try:
                content = self.file_repository.read_file(package_json_path)
                import json
                package_data = json.loads(content)
                if "description" in package_data:
                    return package_data["description"]
            except:
                pass
        
        readme_path = os.path.join(project_path, "README.md")
        if self.file_repository.file_exists(readme_path):
            try:
                content = self.file_repository.read_file(readme_path)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and i > 0:
                        description = line.strip()
                        return description[:200] + ('...' if len(description) > 200 else '')
            except:
                pass
        
        csproj_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith('.csproj'):
                    csproj_files.append(os.path.join(root, file))
        
        if csproj_files:
            try:
                content = self.file_repository.read_file(csproj_files[0])
                desc_match = re.search(r'<Description>([^<]+)</Description>', content)
                if desc_match:
                    return desc_match.group(1)
            except:
                pass
                
        for root, _, files in os.walk(project_path):
            if 'AssemblyInfo.cs' in files:
                try:
                    content = self.file_repository.read_file(os.path.join(root, 'AssemblyInfo.cs'))
                    desc_match = re.search(r'AssemblyDescription\("([^"]+)"\)', content)
                    if desc_match:
                        return desc_match.group(1)
                except:
                    pass
        
        main_files = ["main.py", "index.js", "app.py", "app.js", "Program.cs", "Main.cs", "App.xaml.cs", 
                      "src/main.py", "src/index.js", "src/app.py", "src/app.js", "src/Program.cs", "src/Main.cs"]
        for main_file in main_files:
            main_path = os.path.join(project_path, main_file)
            if self.file_repository.file_exists(main_path):
                try:
                    content = self.file_repository.read_file(main_path)
                    import re
                    doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                    if doc_match:
                        doc_text = doc_match.group(1).strip()
                        if len(doc_text) > 10:
                            lines = doc_text.split('\n')
                            description = lines[0].strip()
                            if not description:
                                for line in lines[1:]:
                                    if line.strip():
                                        description = line.strip()
                                        break
                            return description[:200] + ('...' if len(description) > 200 else '')
                    
                    js_comment = re.search(r'/\*\*(.*?)\*/', content, re.DOTALL)
                    if js_comment:
                        comment_text = js_comment.group(1).strip()
                        comment_text = re.sub(r'^\s*\*\s?', '', comment_text, flags=re.MULTILINE)
                        if len(comment_text) > 10:
                            lines = comment_text.split('\n')
                            description = lines[0].strip()
                            return description[:200] + ('...' if len(description) > 200 else '')
                    
                    cs_comment = re.search(r'///\s*<summary>(.*?)</summary>', content, re.DOTALL)
                    if cs_comment:
                        comment_text = cs_comment.group(1).strip()
                        comment_text = re.sub(r'^\s*///\s?', '', comment_text, flags=re.MULTILINE)
                        if len(comment_text) > 10:
                            lines = comment_text.split('\n')
                            description = ' '.join([line.strip() for line in lines if line.strip()])
                            return description[:200] + ('...' if len(description) > 200 else '')
                except:
                    pass
        
        source_files = self.file_repository.list_files(project_path)
        for file_path in source_files:
            if not self._is_text_file(file_path) or os.path.getsize(file_path) > 50000:
                continue
                
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs']:
                try:
                    content = self.file_repository.read_file(file_path)[:5000]
                    import re
                    
                    if ext == '.py':
                        doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                        if doc_match:
                            doc_text = doc_match.group(1).strip()
                            if len(doc_text) > 30:
                                lines = doc_text.split('\n')
                                description = ' '.join([l.strip() for l in lines[:2] if l.strip()])
                                return description[:200] + ('...' if len(description) > 200 else '')
                    
                    elif ext == '.cs':
                        cs_comment = re.search(r'///\s*<summary>(.*?)</summary>', content, re.DOTALL)
                        if cs_comment:
                            comment_text = cs_comment.group(1).strip()
                            comment_text = re.sub(r'^\s*///\s?', '', comment_text, flags=re.MULTILINE)
                            if len(comment_text) > 10:
                                lines = comment_text.split('\n')
                                description = ' '.join([line.strip() for line in lines if line.strip()])
                                return description[:200] + ('...' if len(description) > 200 else '')
                except:
                    pass
        
        if not description:
            try:
                project_name = os.path.basename(project_path).replace('-', ' ').replace('_', ' ')
                modules = []
                for item in os.listdir(project_path):
                    if item.startswith('.') or item in ['node_modules', 'venv', 'dist', 'build', 'obj', 'bin', '.vs']:
                        continue
                    if os.path.isdir(os.path.join(project_path, item)) and not item.startswith('__'):
                        modules.append(item)
                
                if modules:
                    modules_text = ', '.join([m.replace('_', ' ') for m in modules[:3]])
                    description = f"A {project_name} project with modules for {modules_text}"
                else:
                    description = f"A {project_name} project"
            except:
                pass
        
        return description if description else "Project without description"
        
    def _is_text_file(self, file_path: str) -> bool:
        """
        Checks if a file is a text file.
        
        Args:
            file_path: The path to the file
            
        Returns:
            bool: True if the file is a text file, otherwise False
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
                  '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.rb', '.php', '.sh', '.bat', '.ps1']:
            return True
            
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' not in chunk
        except:
            return False
    
    def _detect_has_tests(self, project_path: str) -> bool:
        """
        Determines the presence of tests in the project.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            bool: True if the project has tests
        """
        test_dirs = ["tests", "test", "__tests__", "spec", "specs"]
        for test_dir in test_dirs:
            if os.path.isdir(os.path.join(project_path, test_dir)):
                return True
        
        return False
    
    def _detect_has_documentation(self, project_path: str) -> bool:
        """
        Determines the presence of documentation in the project.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            bool: True if the project has documentation
        """
        doc_dirs = ["docs", "doc", "documentation", "wiki"]
        for doc_dir in doc_dirs:
            if os.path.isdir(os.path.join(project_path, doc_dir)):
                return True
        
        doc_files = ["README.md", "API.md", "DOCUMENTATION.md"]
        for doc_file in doc_files:
            if self.file_repository.file_exists(os.path.join(project_path, doc_file)):
                return True
        
        return False
    
    def _detect_license_type(self, project_path: str) -> Optional[str]:
        """
        Determines the type of license of the project.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            Optional[str]: The type of license or None
        """
        license_files = [
            "LICENSE", "LICENSE.md", "LICENSE.txt", 
            "COPYING", "COPYING.md", "COPYING.txt"
        ]
        
        for license_file in license_files:
            license_path = os.path.join(project_path, license_file)
            if self.file_repository.file_exists(license_path):
                try:
                    content = self.file_repository.read_file(license_path)
                    return self._determine_license_type(content)
                except:
                    return "Unknown"
        
        package_json_path = os.path.join(project_path, "package.json")
        if self.file_repository.file_exists(package_json_path):
            try:
                content = self.file_repository.read_file(package_json_path)
                import json
                package_data = json.loads(content)
                if "license" in package_data:
                    return package_data["license"]
            except:
                pass
        
        return None
    
    def _determine_license_type(self, content: str) -> str:
        """
        Determines the type of license by the file content.
        
        Args:
            content: The content of the license file
            
        Returns:
            str: The type of license
        """
        content_lower = content.lower()
        
        if "mit license" in content_lower:
            return "MIT"
        elif "apache license" in content_lower:
            return "Apache"
        elif "bsd" in content_lower and "license" in content_lower:
            return "BSD"
        elif "gnu general public license" in content_lower or "gpl" in content_lower:
            return "GPL"
        elif "mozilla public license" in content_lower:
            return "MPL"
        elif "isc" in content_lower and "license" in content_lower:
            return "ISC"
        elif "creative commons" in content_lower:
            return "Creative Commons"
        elif "unlicense" in content_lower:
            return "Unlicense"
        else:
            return "Custom"
    
    def _detect_repository_url(self, project_path: str) -> Optional[str]:
        """
        Determines the URL of the project repository.
        
        Args:
            project_path: The path to the project root
            
        Returns:
            Optional[str]: The URL of the project repository or None
        """
        package_json_path = os.path.join(project_path, "package.json")
        if self.file_repository.file_exists(package_json_path):
            try:
                content = self.file_repository.read_file(package_json_path)
                import json
                package_data = json.loads(content)
                if "repository" in package_data:
                    repo = package_data["repository"]
                    if isinstance(repo, str):
                        return repo
                    elif isinstance(repo, dict) and "url" in repo:
                        return repo["url"]
            except:
                pass
        
        git_config_path = os.path.join(project_path, ".git", "config")
        if self.file_repository.file_exists(git_config_path):
            try:
                content = self.file_repository.read_file(git_config_path)
                url_match = re.search(r'url\s*=\s*([^\n]+)', content)
                if url_match:
                    return url_match.group(1).strip()
            except:
                pass
        
        return None
    
    def _convert_technologies_data(self, tech_data: Dict[str, List[Dict[str, Any]]]) -> List[Technology]:
        """
        Converts technology data to a list of Technology objects.
        
        Args:
            tech_data: The dictionary of technology data
            
        Returns:
            List[Technology]: The list of Technology objects
        """
        result = []
        
        for category, items in tech_data.items():
            for item in items:
                tech = Technology(
                    name=item.get("name", ""),
                    category=category,
                    version=item.get("version"),
                    importance=item.get("importance", 1)
                )
                result.append(tech)
        
        return result 

    def _detect_project_features(self, project_path: str, technologies: List[Technology]) -> List[Feature]:
        """
        Determines the main functions of the project based on the analysis of files and code.
        
        Args:
            project_path: The path to the project root
            technologies: The list of technologies used in the project
            
        Returns:
            List[Feature]: The list of project functions
        """
        from ...domain.entities.project import Feature
        features = []
        
        web_indicators = ['flask', 'django', 'express', 'fastapi', 'router', 'route', 'templates', 'views', 
                         'controllers', 'app.get', 'app.post', 'render', 'request', 'response']
        api_indicators = ['api', 'rest', 'graphql', 'endpoint', 'controller', 'route', 'restful', 
                         '@app.route', '@api', 'router', 'apicontroller']
        cli_indicators = ['cli', 'command', 'argparse', 'click', 'commander', 'yargs', 'parser', 'flag', 
                         'argument', 'option', 'argv']
        db_indicators = ['database', 'db', 'mongo', 'sql', 'postgresql', 'mysql', 'sqlite', 'orm', 
                        'query', 'model', 'entity', 'repository', 'dao']
        ai_indicators = ['model', 'train', 'predict', 'machine learning', 'tensorflow', 'pytorch', 
                        'keras', 'sklearn', 'ml', 'ai', 'neural']
        scraping_indicators = ['scrape', 'crawler', 'spider', 'beautifulsoup', 'selenium', 'requests', 
                              'http', 'html', 'parse', 'extract']
        testing_indicators = ['test', 'spec', 'assert', 'expect', 'should', 'mock', 'stub', 'fixture']
        auth_indicators = ['auth', 'login', 'register', 'password', 'user', 'token', 'jwt', 'oauth', 
                          'credential', 'permission']
        file_processing_indicators = ['file', 'read', 'write', 'open', 'save', 'load', 'import', 'export', 
                                     'csv', 'excel', 'json', 'yaml', 'xml', 'parser']
        async_indicators = ['async', 'await', 'promise', 'coroutine', 'future', 'deferred', 'callback', 'worker']
        
        src_path = os.path.join(project_path, 'src')
        if os.path.isdir(src_path):
            project_dirs = os.listdir(src_path)
        else:
            project_dirs = os.listdir(project_path)
            
        project_dirs = [d.lower() for d in project_dirs]
        
        source_files = []
        for root, _, files in os.walk(project_path):
            if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build']):
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.py', '.js', '.ts', '.java', '.php', '.rb']:
                    source_files.append(os.path.join(root, file))
        
        source_files = source_files[:50]
        
        feature_counters = {
            'web': 0,
            'api': 0,
            'cli': 0,
            'database': 0,
            'ai': 0,
            'scraping': 0,
            'testing': 0,
            'auth': 0,
            'file_processing': 0,
            'async': 0
        }
        
        for file_path in source_files:
            if os.path.getsize(file_path) > 100000:
                continue
                
            try:
                content = self.file_repository.read_file(file_path).lower()
                
                for indicator in web_indicators:
                    if indicator in content:
                        feature_counters['web'] += 1
                
                for indicator in api_indicators:
                    if indicator in content:
                        feature_counters['api'] += 1
                
                for indicator in cli_indicators:
                    if indicator in content:
                        feature_counters['cli'] += 1
                
                for indicator in db_indicators:
                    if indicator in content:
                        feature_counters['database'] += 1
                
                for indicator in ai_indicators:
                    if indicator in content:
                        feature_counters['ai'] += 1
                
                for indicator in scraping_indicators:
                    if indicator in content:
                        feature_counters['scraping'] += 1
                
                for indicator in testing_indicators:
                    if indicator in content:
                        feature_counters['testing'] += 1
                
                for indicator in auth_indicators:
                    if indicator in content:
                        feature_counters['auth'] += 1
                
                for indicator in file_processing_indicators:
                    if indicator in content:
                        feature_counters['file_processing'] += 1
                
                for indicator in async_indicators:
                    if indicator in content:
                        feature_counters['async'] += 1
            except:
                continue
        
        for dir_name in project_dirs:
            if any(indicator in dir_name for indicator in web_indicators):
                feature_counters['web'] += 5
            if any(indicator in dir_name for indicator in api_indicators):
                feature_counters['api'] += 5
            if any(indicator in dir_name for indicator in cli_indicators):
                feature_counters['cli'] += 5
            if any(indicator in dir_name for indicator in db_indicators):
                feature_counters['database'] += 5
            if any(indicator in dir_name for indicator in ai_indicators):
                feature_counters['ai'] += 5
            if any(indicator in dir_name for indicator in scraping_indicators):
                feature_counters['scraping'] += 5
            if any(indicator in dir_name for indicator in testing_indicators):
                feature_counters['testing'] += 5
            if any(indicator in dir_name for indicator in auth_indicators):
                feature_counters['auth'] += 5
            if any(indicator in dir_name for indicator in file_processing_indicators):
                feature_counters['file_processing'] += 5
            if any(indicator in dir_name for indicator in async_indicators):
                feature_counters['async'] += 5
        
        for tech in technologies:
            tech_name = tech.name.lower()
            if tech_name in ['flask', 'django', 'express', 'fastapi', 'vue.js', 'react', 'angular']:
                feature_counters['web'] += 10
            if 'api' in tech_name or tech_name in ['graphql', 'rest framework', 'restful']:
                feature_counters['api'] += 8
            if tech_name in ['click', 'argparse', 'commander', 'yargs', 'cobra']:
                feature_counters['cli'] += 10
            if any(db in tech_name for db in ['sql', 'mongo', 'postgres', 'mysql', 'sqlite', 'orm']):
                feature_counters['database'] += 10
            if tech_name in ['tensorflow', 'pytorch', 'keras', 'sklearn', 'pandas', 'numpy']:
                feature_counters['ai'] += 10
            if tech_name in ['beautifulsoup', 'selenium', 'requests', 'scrapy', 'puppeteer']:
                feature_counters['scraping'] += 10
            if tech_name in ['pytest', 'jest', 'mocha', 'junit', 'phpunit']:
                feature_counters['testing'] += 8
            if tech_name in ['jwt', 'passport', 'oauth', 'auth0', 'authlib']:
                feature_counters['auth'] += 8
        
        feature_descriptions = {
            'web': ('Web Application', 'Provides a web interface for user interaction'),
            'api': ('API', 'Provides a programming interface for interaction with other systems'),
            'cli': ('Command Line Interface', 'Allows managing functionality through terminal commands'),
            'database': ('Database Operations', 'Storage and management of data in databases'),
            'ai': ('Machine Learning/AI', 'Uses machine learning or artificial intelligence algorithms'),
            'scraping': ('Web Scraping', 'Extraction of data from websites'),
            'testing': ('Testing', 'Contains automated code tests'),
            'auth': ('Authentication and Authorization', 'User management, access rights, and authentication'),
            'file_processing': ('File Processing', 'Working with files of various formats'),
            'async': ('Asynchronous Processing', 'Uses asynchronous programming for parallel operations')
        }
        
        for feature_type, counter in feature_counters.items():
            threshold = 8 if feature_type in ['web', 'cli', 'api'] else 5
            if counter >= threshold:
                name, description = feature_descriptions[feature_type]
                priority = 5 if counter >= 15 else (4 if counter >= 10 else 3)
                features.append(Feature(
                    name=name,
                    description=description,
                    category=feature_type,
                    priority=priority
                ))
        
        project_name_lower = os.path.basename(project_path).lower()
        
        if 'download' in project_name_lower or 'downloader' in project_name_lower:
            features.append(Feature(
                name='Content Download',
                description='Download files or content from external sources',
                category='download',
                priority=5
            ))
            
        if 'youtube' in project_name_lower:
            features.append(Feature(
                name='YouTube Integration',
                description='Working with YouTube API or downloading content from YouTube',
                category='integration',
                priority=5
            ))
            
        if not features:
            words = project_name_lower.replace('-', ' ').replace('_', ' ').split()
            if len(words) > 1:
                action_word = words[0]
                subject_words = ' '.join(words[1:])
                features.append(Feature(
                    name=f"{action_word.capitalize()} {subject_words}",
                    description=f"Application for working with {subject_words}",
                    category="general",
                    priority=3
                ))
        
        return features 

    def _detect_architecture_description(self, project_path: str, technologies: List[Technology], structure: Dict[str, Any]) -> str:
        """
        Determines and describes the architecture of the project based on its structure and technologies.
        
        Args:
            project_path: The path to the project
            technologies: The list of project technologies
            structure: The data about the project structure
            
        Returns:
            str: The description of the project architecture
        """
        architecture_components = []
        
        src_path = os.path.join(project_path, 'src')
        if os.path.isdir(src_path):
            project_dirs = [os.path.join(src_path, d) for d in os.listdir(src_path) 
                           if os.path.isdir(os.path.join(src_path, d))]
        else:
            project_dirs = [os.path.join(project_path, d) for d in os.listdir(project_path) 
                           if os.path.isdir(os.path.join(project_path, d)) and not d.startswith('.')]
            
        dir_names = [os.path.basename(d).lower() for d in project_dirs]
        
        if all(d in dir_names for d in ['models', 'views', 'controllers']):
            architecture_components.append("MVC (Model-View-Controller)")
        
        if all(d in dir_names for d in ['models', 'views', 'viewmodels']):
            architecture_components.append("MVVM (Model-View-ViewModel)")
        
        if all(d in dir_names for d in ['models', 'views', 'presenters']):
            architecture_components.append("MVP (Model-View-Presenter)")
        
        if any(d in dir_names for d in ['domain', 'entities']):
            if any(d in dir_names for d in ['application', 'usecases', 'use_cases']):
                if any(d in dir_names for d in ['infrastructure', 'frameworks']):
                    architecture_components.append("Clean Architecture")
                    
        layer_count = 0
        for layer in ['data', 'domain', 'application', 'presentation', 'ui', 'persistence']:
            if layer in dir_names:
                layer_count += 1
        if layer_count >= 2:
            architecture_components.append("Layered Architecture")
        
        if 'services' in dir_names:
            services_path = os.path.join(project_path, 'services') if 'services' in os.listdir(project_path) else os.path.join(src_path, 'services')
            if os.path.isdir(services_path) and len([d for d in os.listdir(services_path) if os.path.isdir(os.path.join(services_path, d))]) > 2:
                architecture_components.append("Service-Oriented Architecture")
        
        if 'repositories' in dir_names:
            architecture_components.append("Repository Pattern")
        
        has_factory = False
        for project_dir in project_dirs:
            for root, _, files in os.walk(project_dir):
                for file in files:
                    if 'factory' in file.lower():
                        has_factory = True
                        break
                if has_factory:
                    break
            if has_factory:
                break
        if has_factory:
            architecture_components.append("Factory Pattern")
            
        tech_names = [tech.name.lower() for tech in technologies]
        if 'django' in tech_names:
            architecture_components.append("Django MTV (Model-Template-View)")
        if 'flask' in tech_names or 'fastapi' in tech_names:
            architecture_components.append("REST API")
        if 'express' in tech_names:
            architecture_components.append("Express.js Middleware Architecture")
        if 'react' in tech_names:
            architecture_components.append("Component-Based Architecture")
            
        if 'domain' in dir_names:
            domain_path = os.path.join(project_path, 'domain') if 'domain' in os.listdir(project_path) else os.path.join(src_path, 'domain')
            if os.path.isdir(domain_path):
                domain_contents = os.listdir(domain_path)
                if any(n in [d.lower() for d in domain_contents] for n in ['aggregates', 'entities', 'value_objects', 'services']):
                    architecture_components.append("Domain-Driven Design (DDD)")
        
        if not architecture_components:
            tech_arch = [tech.name for tech in technologies if tech.category == 'architecture']
            if tech_arch:
                architecture_description = f"The project uses the following architectural approaches: {', '.join(tech_arch)}."
            else:
                architecture_description = "Standard application architecture."
        else:
            architecture_description = f"The project uses the following architectural approaches and patterns: {', '.join(architecture_components)}."
            
        try:
            if 'src' in os.listdir(project_path):
                src_dirs = [d for d in os.listdir(os.path.join(project_path, 'src')) 
                           if os.path.isdir(os.path.join(project_path, 'src', d))]
                if src_dirs:
                    architecture_description += f" Main modules: {', '.join(src_dirs)}."
        except:
            pass
            
        return architecture_description 

    def _enrich_technologies_from_source(self, project_path: str, tech_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes source files to detect imports and library usage.
        
        Args:
            project_path: The path to the project root
            tech_data: Current technology data
            
        Returns:
            Dict[str, Any]: Enriched technology data
        """
        python_libraries = {
            'requests': ('networking', 'Working with HTTP requests'),
            'flask': ('framework', 'Web framework'),
            'django': ('framework', 'Web framework'),
            'fastapi': ('framework', 'Web framework for API'),
            'sqlalchemy': ('database', 'ORM for SQL'),
            'pandas': ('data-science', 'Data analysis'),
            'numpy': ('data-science', 'Scientific computing'),
            'matplotlib': ('data-science', 'Data visualization'),
            'tensorflow': ('ai', 'Machine learning'),
            'pytorch': ('ai', 'Machine learning'),
            'scikit-learn': ('ai', 'Machine learning'),
            'beautifulsoup': ('web-scraping', 'HTML parsing'),
            'selenium': ('web-automation', 'Browser automation'),
            'pytest': ('testing', 'Testing'),
            'celery': ('async', 'Asynchronous tasks'),
            'pika': ('messaging', 'Working with RabbitMQ'),
            'pillow': ('imaging', 'Image processing'),
            'boto3': ('cloud', 'AWS SDK'),
            'google-cloud': ('cloud', 'Google Cloud SDK'),
            'azure': ('cloud', 'Azure SDK'),
            'ffmpeg': ('multimedia', 'Video/audio processing'),
            'pytube': ('youtube', 'Download from YouTube'),
            'youtube_dl': ('youtube', 'Download from YouTube'),
        }
        
        js_libraries = {
            'react': ('frontend', 'UI library'),
            'angular': ('frontend', 'SPA framework'),
            'vue': ('frontend', 'Progressive framework'),
            'express': ('backend', 'Web framework for Node.js'),
            'axios': ('networking', 'HTTP client'),
            'mongoose': ('database', 'ODM for MongoDB'),
            'sequelize': ('database', 'ORM for SQL'),
            'jest': ('testing', 'Testing'),
            'mocha': ('testing', 'Testing'),
            'webpack': ('build-tool', 'Project build'),
            'babel': ('build-tool', 'JavaScript transpilation'),
            'redux': ('state-management', 'State management'),
            'next': ('framework', 'React framework'),
            'gatsby': ('framework', 'React framework for static sites'),
            'youtube-api': ('youtube', 'YouTube API'),
            'ytdl-core': ('youtube', 'Download from YouTube'),
        }
        
        source_files = []
        for root, _, files in os.walk(project_path):
            if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build']):
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.py', '.js', '.ts']:
                    source_files.append(os.path.join(root, file))
                
        source_files = source_files[:50]
        
        found_libraries = {}
        
        for file_path in source_files:
            try:
                content = self.file_repository.read_file(file_path).lower()
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == '.py':
                    import re
                    import_patterns = [
                        r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                        r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
                    ]
                    
                    for pattern in import_patterns:
                        for match in re.finditer(pattern, content):
                            lib = match.group(1)
                            for known_lib, (category, description) in python_libraries.items():
                                if lib == known_lib or lib.startswith(known_lib + '.'):
                                    found_libraries[known_lib] = (category, description)
                
                elif ext in ['.js', '.ts']:
                    import re
                    import_patterns = [
                        r'import.*from\s+["\']([^"\']+)["\']',
                        r'require\(["\']([^"\']+)["\']',
                    ]
                    
                    for pattern in import_patterns:
                        for match in re.finditer(pattern, content):
                            lib = match.group(1)
                            if '/' in lib:
                                lib = lib.split('/')[0]
                            if lib.startswith('@'):
                                parts = lib.split('/')
                                if len(parts) > 1:
                                    lib = parts[0] + '/' + parts[1]
                            
                            for known_lib, (category, description) in js_libraries.items():
                                if lib == known_lib or known_lib in lib:
                                    found_libraries[known_lib] = (category, description)
            except:
                continue
        
        for lib, (category, _) in found_libraries.items():
            mapped_category = self._map_library_category_to_tech_category(category)
            
            exists = False
            for tech in tech_data.get(mapped_category, []):
                if isinstance(tech, dict) and tech.get('name', '').lower() == lib.lower():
                    exists = True
                    break
                elif isinstance(tech, str) and tech.lower() == lib.lower():
                    exists = True
                    break
            
            if not exists:
                if mapped_category not in tech_data:
                    tech_data[mapped_category] = []
                tech_data[mapped_category].append({
                    'name': lib,
                    'importance': 3
                })
        
        return tech_data
    
    def _map_library_category_to_tech_category(self, lib_category: str) -> str:
        """
        Maps the library category to the technology category.
        
        Args:
            lib_category: The library category
            
        Returns:
            str: The technology category
        """
        mapping = {
            'framework': 'framework',
            'frontend': 'frontend',
            'backend': 'backend',
            'database': 'database',
            'networking': 'backend',
            'data-science': 'other',
            'ai': 'other',
            'web-scraping': 'backend',
            'web-automation': 'backend',
            'testing': 'testing',
            'async': 'backend',
            'messaging': 'backend',
            'imaging': 'other',
            'cloud': 'devops',
            'build-tool': 'devops',
            'state-management': 'frontend',
            'multimedia': 'other',
            'youtube': 'backend'
        }
        
        return mapping.get(lib_category, 'other') 