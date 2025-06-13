"""Technology analyzer."""
import os
import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Set, Optional, Tuple
import toml
import yaml
import fnmatch

from ...domain.ports.analyzers import TechnologyAnalyzerPort
from ...domain.ports.repositories import FileRepositoryPort, ConfigRepositoryPort


class TechnologyAnalyzer(TechnologyAnalyzerPort):
    """Technology analyzer."""
    
    def __init__(self, file_repository: FileRepositoryPort, config_repository: ConfigRepositoryPort):
        """
        Initializes the technology analyzer.
        
        Args:
            file_repository: File repository
            config_repository: Configuration repository
        """
        self.file_repository = file_repository
        self.config_repository = config_repository
    
    def detect_technologies(self, project_path: str) -> Dict[str, Any]:
        """
        Determines the technologies used in the project.
        
        Args:
            project_path: The path to the project root
        
        Returns:
            Dict[str, Any]: The dictionary of detected technologies and their metadata
        """
        result = {
            "language": [],
            "framework": [],
            "database": [],
            "frontend": [],
            "backend": [],
            "devops": [],
            "testing": [],
            "architecture": [],
            "other": []
        }
        
        self._analyze_file_extensions(project_path, result)
        
        self._analyze_package_files(project_path, result)
        
        self._analyze_config_files(project_path, result)
        
        self._analyze_project_files(project_path, result)
        
        return result
    
    def _analyze_file_extensions(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes file extensions to determine programming languages.
        
        Args:
            project_path: The path to the project
            result: The dictionary for accumulating results
        """
        extensions_config = self.config_repository.get_config("analyzers.file_extensions")
        
        extension_counts = {}
        
        for root, _, files in os.walk(project_path):
            if _is_ignored_dir(root):
                continue
                
            for file in files:
                if _is_ignored_file(file):
                    continue
                
                _, ext = os.path.splitext(file)
                ext = ext.lstrip('.')
                
                if ext:
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        languages = {}
        for ext, count in extension_counts.items():
            if ext in extensions_config:
                language = extensions_config[ext]
                languages[language] = languages.get(language, 0) + count
        
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        
        for i, (language, count) in enumerate(sorted_languages):
            importance = 5 if i == 0 else (4 if i == 1 else (3 if i < 4 else 2))
            result["language"].append({
                "name": language,
                "count": count,
                "importance": importance
            })
    
    def _analyze_package_files(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes package files and dependencies.
        
        Args:
            project_path: The path to the project
            result: The dictionary for accumulating results
        """
        package_files_config = self.config_repository.get_config("analyzers.package_files")
        
        requirements_path = os.path.join(project_path, "requirements.txt")
        if self.file_repository.file_exists(requirements_path):
            packages = self._parse_requirements_txt(requirements_path)
            self._process_python_packages(packages, result)
        
        setup_py_path = os.path.join(project_path, "setup.py")
        if self.file_repository.file_exists(setup_py_path):
            self._add_technology_if_not_exists(result, "language", "Python", 5)
        
        pyproject_toml_path = os.path.join(project_path, "pyproject.toml")
        if self.file_repository.file_exists(pyproject_toml_path):
            self._add_technology_if_not_exists(result, "language", "Python", 5)
            try:
                content = self.file_repository.read_file(pyproject_toml_path)
                pyproject_data = toml.loads(content)
                
                if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
                    poetry_deps = pyproject_data["tool"]["poetry"].get("dependencies", {})
                    self._add_technology_if_not_exists(result, "devops", "Poetry", 3)
                    
                    for dep_name, dep_version in poetry_deps.items():
                        if dep_name.lower() == "django":
                            self._add_technology_if_not_exists(result, "framework", "Django", 5)
                        elif dep_name.lower() == "flask":
                            self._add_technology_if_not_exists(result, "framework", "Flask", 5)
                        elif dep_name.lower() == "fastapi":
                            self._add_technology_if_not_exists(result, "framework", "FastAPI", 5)
            except Exception as e:
                print(f"Error parsing pyproject.toml: {e}")
        
        package_json_path = os.path.join(project_path, "package.json")
        if self.file_repository.file_exists(package_json_path):
            packages = self._parse_package_json(package_json_path)
            self._process_js_packages(packages, result)
        
        cargo_toml_path = os.path.join(project_path, "Cargo.toml")
        if self.file_repository.file_exists(cargo_toml_path):
            packages = self._parse_cargo_toml(cargo_toml_path)
            self._process_rust_packages(packages, result)
        
        pom_xml_path = os.path.join(project_path, "pom.xml")
        if self.file_repository.file_exists(pom_xml_path):
            dependencies = self._parse_pom_xml(pom_xml_path)
            self._process_java_packages(dependencies, result)
            self._add_technology_if_not_exists(result, "devops", "Maven", 3)
        
        build_gradle_path = os.path.join(project_path, "build.gradle")
        if self.file_repository.file_exists(build_gradle_path):
            self._add_technology_if_not_exists(result, "devops", "Gradle", 3)
            
            content = self.file_repository.read_file(build_gradle_path)
            if "kotlin" in content.lower():
                self._add_technology_if_not_exists(result, "language", "Kotlin", 5)
            else:
                self._add_technology_if_not_exists(result, "language", "Java", 5)
                
            if "org.springframework.boot" in content:
                self._add_technology_if_not_exists(result, "framework", "Spring Boot", 5)
            if "org.springframework" in content and "org.springframework.boot" not in content:
                self._add_technology_if_not_exists(result, "framework", "Spring Framework", 5)
        
        build_gradle_kts_path = os.path.join(project_path, "build.gradle.kts")
        if self.file_repository.file_exists(build_gradle_kts_path):
            self._add_technology_if_not_exists(result, "language", "Kotlin", 5)
            self._add_technology_if_not_exists(result, "devops", "Gradle", 3)
    
    def _analyze_config_files(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Анализирует конфигурационные файлы проекта.
        
        Args:
            project_path: Путь к корню проекта
            result: Словарь для накопления результатов
        """
        project_files_config = self.config_repository.get_config("analyzers.project_files")
        
        for file_pattern, technology in project_files_config.items():
            if '*' in file_pattern or '?' in file_pattern:
                found = False
                for root, _, files in os.walk(project_path):
                    if _is_ignored_dir(root):
                        continue
                    
                    for file in files:
                        if fnmatch.fnmatch(file.lower(), file_pattern.lower()):
                            found = True
                            break
                    
                    if found:
                        break
                
                if found:
                    category = self._determine_technology_category(technology)
                    self._add_technology_if_not_exists(result, category, technology, 3)
            else:
                if '/' in file_pattern:
                    file_path = os.path.join(project_path, *file_pattern.split('/'))
                    if self.file_repository.file_exists(file_path) or os.path.isdir(os.path.join(project_path, file_pattern)):
                        category = self._determine_technology_category(technology)
                        self._add_technology_if_not_exists(result, category, technology, 3)
                else:
                    if self.file_repository.file_exists(os.path.join(project_path, file_pattern)):
                        category = self._determine_technology_category(technology)
                        self._add_technology_if_not_exists(result, category, technology, 3)
                    
                    if file_pattern.startswith('.'):
                        file_no_dot = file_pattern[1:]
                        if self.file_repository.file_exists(os.path.join(project_path, file_no_dot)):
                            category = self._determine_technology_category(technology)
                            self._add_technology_if_not_exists(result, category, technology, 3)
        
        self._check_devops_tools(project_path, result)
        
        self._check_framework_directories(project_path, result)

    def _check_devops_tools(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Проверяет наличие DevOps инструментов и конфигураций.
        
        Args:
            project_path: Путь к корню проекта
            result: Словарь для накопления результатов
        """
        if self.file_repository.file_exists(os.path.join(project_path, "Dockerfile")) or \
           self.file_repository.file_exists(os.path.join(project_path, "docker-compose.yml")) or \
           self.file_repository.file_exists(os.path.join(project_path, "docker-compose.yaml")):
            self._add_technology_if_not_exists(result, "devops", "Docker", 4)
        
        if any(self.file_repository.file_exists(os.path.join(project_path, k_file)) for k_file in 
               ["kubernetes.yaml", "kubernetes.yml", "k8s.yaml", "k8s.yml", "deployment.yaml", "service.yaml"]):
            self._add_technology_if_not_exists(result, "devops", "Kubernetes", 4)
        
        if os.path.isdir(os.path.join(project_path, "helm")) or \
           os.path.isdir(os.path.join(project_path, "charts")):
            self._add_technology_if_not_exists(result, "devops", "Helm", 3)
        
        if os.path.isdir(os.path.join(project_path, ".github", "workflows")):
            self._add_technology_if_not_exists(result, "devops", "GitHub Actions", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, ".gitlab-ci.yml")) or \
             self.file_repository.file_exists(os.path.join(project_path, ".gitlab-ci.yaml")):
            self._add_technology_if_not_exists(result, "devops", "GitLab CI", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, ".travis.yml")) or \
             self.file_repository.file_exists(os.path.join(project_path, ".travis.yaml")):
            self._add_technology_if_not_exists(result, "devops", "Travis CI", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, "Jenkinsfile")):
            self._add_technology_if_not_exists(result, "devops", "Jenkins", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, "azure-pipelines.yml")) or \
             self.file_repository.file_exists(os.path.join(project_path, "azure-pipelines.yaml")):
            self._add_technology_if_not_exists(result, "devops", "Azure Pipelines", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, "appveyor.yml")) or \
             self.file_repository.file_exists(os.path.join(project_path, "appveyor.yaml")):
            self._add_technology_if_not_exists(result, "devops", "AppVeyor", 3)
        elif self.file_repository.file_exists(os.path.join(project_path, "buildspec.yml")) or \
             self.file_repository.file_exists(os.path.join(project_path, "buildspec.yaml")):
            self._add_technology_if_not_exists(result, "devops", "AWS CodeBuild", 3)
        
        if any(self.file_repository.file_exists(os.path.join(project_path, tf_file)) for tf_file in 
               ["main.tf", "variables.tf", "terraform.tf"]):
            self._add_technology_if_not_exists(result, "devops", "Terraform", 4)
        
        if self.file_repository.file_exists(os.path.join(project_path, "ansible.cfg")) or \
           os.path.isdir(os.path.join(project_path, "roles")) or \
           any(self.file_repository.file_exists(os.path.join(project_path, ansible_file)) for ansible_file in 
               ["playbook.yml", "playbook.yaml", "inventory.ini", "hosts"]):
            self._add_technology_if_not_exists(result, "devops", "Ansible", 4)
        
        if self.file_repository.file_exists(os.path.join(project_path, "pulumi.yaml")) or \
           self.file_repository.file_exists(os.path.join(project_path, "Pulumi.yaml")):
            self._add_technology_if_not_exists(result, "devops", "Pulumi", 4)

    def _check_framework_directories(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Проверяет структуру директорий для определения фреймворков и библиотек.
        
        Args:
            project_path: Путь к корню проекта
            result: Словарь для накопления результатов
        """
        directory_to_tech = {
            "node_modules": {"name": "Node.js", "category": "language", "importance": 3},
            "vendor": {"name": "Composer (PHP)", "category": "devops", "importance": 3},
            "migrations": {"name": "Database Migrations", "category": "database", "importance": 3},
            "controllers": {"name": "MVC Architecture", "category": "architecture", "importance": 3},
            "views": {"name": "MVC Architecture", "category": "architecture", "importance": 3},
            "models": {"name": "MVC Architecture", "category": "architecture", "importance": 3},
            "templates": {"name": "Template Engine", "category": "frontend", "importance": 3},
            "components": {"name": "Component-based Framework", "category": "frontend", "importance": 3},
            "pages": {"name": "Page-based Framework", "category": "frontend", "importance": 3},
            "routes": {"name": "Routing", "category": "backend", "importance": 3},
            "middlewares": {"name": "Middleware Pattern", "category": "backend", "importance": 3},
            "middleware": {"name": "Middleware Pattern", "category": "backend", "importance": 3},
            "hooks": {"name": "Hook System", "category": "framework", "importance": 3},
            "services": {"name": "Service Layer", "category": "architecture", "importance": 3},
            "repositories": {"name": "Repository Pattern", "category": "architecture", "importance": 3},
            "providers": {"name": "Provider Pattern", "category": "architecture", "importance": 3},
            "tests": {"name": "Automated Tests", "category": "testing", "importance": 3},
            "test": {"name": "Automated Tests", "category": "testing", "importance": 3},
            "spec": {"name": "Automated Tests", "category": "testing", "importance": 3},
            "scripts": {"name": "Script Collection", "category": "devops", "importance": 2},
            "docs": {"name": "Documentation", "category": "other", "importance": 2},
            "artifacts": {"name": "Build Artifacts", "category": "devops", "importance": 2},
            "dist": {"name": "Distribution", "category": "devops", "importance": 2},
            "build": {"name": "Build Output", "category": "devops", "importance": 2},
            "bin": {"name": "Binaries", "category": "devops", "importance": 2},
            "obj": {"name": ".NET Object Files", "category": "devops", "importance": 2},
            "packages": {"name": "Package Management", "category": "devops", "importance": 2},
            "modules": {"name": "Module System", "category": "architecture", "importance": 2},
            "api": {"name": "API", "category": "backend", "importance": 3},
            "public": {"name": "Public Assets", "category": "frontend", "importance": 2},
            "static": {"name": "Static Assets", "category": "frontend", "importance": 2},
            "assets": {"name": "Asset Files", "category": "frontend", "importance": 2},
            "styles": {"name": "CSS Styles", "category": "frontend", "importance": 2},
            "images": {"name": "Image Files", "category": "frontend", "importance": 2},
            "fonts": {"name": "Font Files", "category": "frontend", "importance": 2},
            "config": {"name": "Configuration", "category": "devops", "importance": 2},
            "configs": {"name": "Configuration", "category": "devops", "importance": 2},
            "configuration": {"name": "Configuration", "category": "devops", "importance": 2},
            "environments": {"name": "Environment Config", "category": "devops", "importance": 2}
        }
        
        for root, dirs, _ in os.walk(project_path):
            if len(root.replace(project_path, '').strip(os.path.sep).split(os.path.sep)) > 2:
                continue
                
            if _is_ignored_dir(root):
                continue
                
            for dir_name in dirs:
                dir_name_lower = dir_name.lower()
                
                if dir_name_lower.startswith('.'):
                    continue
                
                if dir_name_lower in directory_to_tech:
                    tech_info = directory_to_tech[dir_name_lower]
                    self._add_technology_if_not_exists(
                        result, 
                        tech_info["category"],
                        tech_info["name"],
                        tech_info["importance"]
                    )
                
                if dir_name_lower == "angular":
                    self._add_technology_if_not_exists(result, "frontend", "Angular", 4)
                elif dir_name_lower == "react":
                    self._add_technology_if_not_exists(result, "frontend", "React", 4)
                elif dir_name_lower == "vue":
                    self._add_technology_if_not_exists(result, "frontend", "Vue.js", 4)
                elif dir_name_lower == "django":
                    self._add_technology_if_not_exists(result, "framework", "Django", 4)
                elif dir_name_lower == "flask":
                    self._add_technology_if_not_exists(result, "framework", "Flask", 4)
                elif dir_name_lower == "spring":
                    self._add_technology_if_not_exists(result, "framework", "Spring", 4)
                elif dir_name_lower == "laravel":
                    self._add_technology_if_not_exists(result, "framework", "Laravel", 4)
                elif dir_name_lower == "express":
                    self._add_technology_if_not_exists(result, "backend", "Express.js", 4)
                elif dir_name_lower == "react-native":
                    self._add_technology_if_not_exists(result, "framework", "React Native", 4)
                elif dir_name_lower == "flutter":
                    self._add_technology_if_not_exists(result, "framework", "Flutter", 4)
    
    def _parse_requirements_txt(self, path: str) -> List[Dict[str, str]]:
        """
        Парсит файл requirements.txt и возвращает список пакетов.
        
        Args:
            path: Путь к файлу requirements.txt
            
        Returns:
            List[Dict[str, str]]: Список пакетов с именем и версией
        """
        packages = []
        try:
            content = self.file_repository.read_file(path)
            
            for line in content.splitlines():
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if "==" in line:
                    name, version = line.split("==", 1)
                elif ">=" in line:
                    name, version = line.split(">=", 1)
                elif "<=" in line:
                    name, version = line.split("<=", 1)
                elif "~=" in line:
                    name, version = line.split("~=", 1)
                else:
                    name = line
                    version = ""
                
                name = name.strip()
                if version:
                    version = version.strip()
                
                packages.append({
                    "name": name,
                    "version": version
                })
        except Exception as e:
            print(f"Error parsing requirements.txt: {e}")
        
        return packages
    
    def _parse_package_json(self, path: str) -> Dict[str, Any]:
        """
        Parses the package.json file and returns the dependency object.
        
        Args:
            path: Путь к файлу package.json
            
        Returns:
            Dict[str, Any]: Information about the project dependencies
        """
        try:
            content = self.file_repository.read_file(path)
            data = json.loads(content)
            return {
                "name": data.get("name", ""),
                "dependencies": data.get("dependencies", {}),
                "devDependencies": data.get("devDependencies", {}),
                "scripts": data.get("scripts", {}),
                "all_dependencies": {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {})
                }
            }
        except Exception as e:
            print(f"Error parsing package.json: {e}")
            return {
                "name": "",
                "dependencies": {},
                "devDependencies": {},
                "scripts": {},
                "all_dependencies": {}
            }
    
    def _parse_cargo_toml(self, path: str) -> Dict[str, Any]:
        """
        Parses the Cargo.toml file for Rust projects.
        
        Args:
            path: Путь к файлу Cargo.toml
            
        Returns:
            Dict[str, Any]: Information about the project dependencies
        """
        try:
            content = self.file_repository.read_file(path)
            data = toml.loads(content)
            
            dependencies = data.get("dependencies", {})
            dev_dependencies = data.get("dev-dependencies", {})
            
            return {
                "name": data.get("package", {}).get("name", ""),
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies,
                "all_dependencies": {**dependencies, **dev_dependencies}
            }
        except Exception as e:
            print(f"Error parsing Cargo.toml: {e}")
            return {
                "name": "",
                "dependencies": {},
                "dev_dependencies": {},
                "all_dependencies": {}
            }
    
    def _process_python_packages(self, packages: List[Dict[str, str]], result: Dict[str, List[Any]]) -> None:
        """
        Processes Python project packages and adds the corresponding technologies.
        
        Args:
            packages: List of packages
            result: Dictionary for accumulating results
        """
        self._add_technology_if_not_exists(result, "language", "Python", 5)
        
        frameworks = {
            "django": {"category": "framework", "importance": 5, "name": "Django"},
            "flask": {"category": "framework", "importance": 5, "name": "Flask"},
            "fastapi": {"category": "framework", "importance": 5, "name": "FastAPI"},
            "tornado": {"category": "framework", "importance": 4, "name": "Tornado"},
            "sanic": {"category": "framework", "importance": 4, "name": "Sanic"},
            "pyramid": {"category": "framework", "importance": 4, "name": "Pyramid"},
            "aiohttp": {"category": "framework", "importance": 4, "name": "AIOHTTP"},
            "sqlalchemy": {"category": "database", "importance": 4, "name": "SQLAlchemy"},
            "django-rest-framework": {"category": "backend", "importance": 4, "name": "Django REST Framework"},
            "djangorestframework": {"category": "backend", "importance": 4, "name": "Django REST Framework"},
            "alembic": {"category": "database", "importance": 3, "name": "Alembic"},
            "pytest": {"category": "testing", "importance": 4, "name": "PyTest"},
            "unittest": {"category": "testing", "importance": 3, "name": "unittest"},
            "selenium": {"category": "testing", "importance": 3, "name": "Selenium"},
            "behave": {"category": "testing", "importance": 3, "name": "Behave"},
            "celery": {"category": "backend", "importance": 4, "name": "Celery"},
            "redis": {"category": "database", "importance": 3, "name": "Redis"},
            "pymongo": {"category": "database", "importance": 3, "name": "MongoDB (PyMongo)"},
            "psycopg2": {"category": "database", "importance": 3, "name": "PostgreSQL"},
            "psycopg2-binary": {"category": "database", "importance": 3, "name": "PostgreSQL"},
            "pymysql": {"category": "database", "importance": 3, "name": "MySQL"},
            "mysqlclient": {"category": "database", "importance": 3, "name": "MySQL"},
        }
        
        for package in packages:
            name = package["name"].lower()
            
            if name in frameworks:
                lib_info = frameworks[name]
                self._add_technology_if_not_exists(
                    result,
                    lib_info["category"],
                    lib_info["name"],
                    lib_info["importance"]
                )
            
            if name.startswith("django"):
                self._add_technology_if_not_exists(result, "framework", "Django", 5)
                
            if name.startswith("flask"):
                self._add_technology_if_not_exists(result, "framework", "Flask", 5)
                
            if name == "fastapi":
                self._add_technology_if_not_exists(result, "framework", "FastAPI", 5)
    
    def _process_js_packages(self, package_data: Dict[str, Any], result: Dict[str, List[Any]]) -> None:
        """
        Processes JavaScript/Node.js project dependencies and adds the corresponding technologies.
        
        Args:
            package_data: Data from package.json
            result: Dictionary for accumulating results
        """
        deps = package_data["all_dependencies"]
        
        is_frontend = False
        is_backend = False
        is_fullstack = False
        
        frontend_frameworks = {
            "react": {"category": "frontend", "importance": 5, "name": "React"},
            "vue": {"category": "frontend", "importance": 5, "name": "Vue.js"},
            "angular": {"category": "frontend", "importance": 5, "name": "Angular"},
            "svelte": {"category": "frontend", "importance": 5, "name": "Svelte"},
            "next": {"category": "frontend", "importance": 5, "name": "Next.js"},
            "nuxt": {"category": "frontend", "importance": 5, "name": "Nuxt.js"},
            "gatsby": {"category": "frontend", "importance": 4, "name": "Gatsby"},
            "@angular/core": {"category": "frontend", "importance": 5, "name": "Angular"},
            "jquery": {"category": "frontend", "importance": 3, "name": "jQuery"},
            "bootstrap": {"category": "frontend", "importance": 3, "name": "Bootstrap"},
            "tailwindcss": {"category": "frontend", "importance": 4, "name": "Tailwind CSS"},
        }
        
        backend_frameworks = {
            "express": {"category": "backend", "importance": 5, "name": "Express.js"},
            "koa": {"category": "backend", "importance": 5, "name": "Koa.js"},
            "fastify": {"category": "backend", "importance": 4, "name": "Fastify"},
            "nest": {"category": "backend", "importance": 5, "name": "NestJS"},
            "@nestjs/core": {"category": "backend", "importance": 5, "name": "NestJS"},
            "hapi": {"category": "backend", "importance": 4, "name": "Hapi.js"},
            "feathers": {"category": "backend", "importance": 4, "name": "Feathers.js"},
            "socket.io": {"category": "backend", "importance": 3, "name": "Socket.IO"},
            "apollo-server": {"category": "backend", "importance": 4, "name": "Apollo Server"},
        }
        
        database_libs = {
            "mongoose": {"category": "database", "importance": 4, "name": "MongoDB (Mongoose)"},
            "mongodb": {"category": "database", "importance": 4, "name": "MongoDB"},
            "sequelize": {"category": "database", "importance": 4, "name": "SQL (Sequelize)"},
            "typeorm": {"category": "database", "importance": 4, "name": "TypeORM"},
            "prisma": {"category": "database", "importance": 4, "name": "Prisma"},
            "pg": {"category": "database", "importance": 3, "name": "PostgreSQL"},
            "mysql": {"category": "database", "importance": 3, "name": "MySQL"},
            "sqlite3": {"category": "database", "importance": 3, "name": "SQLite"},
            "redis": {"category": "database", "importance": 3, "name": "Redis"},
        }
        
        testing_libs = {
            "jest": {"category": "testing", "importance": 4, "name": "Jest"},
            "mocha": {"category": "testing", "importance": 4, "name": "Mocha"},
            "chai": {"category": "testing", "importance": 3, "name": "Chai"},
            "jasmine": {"category": "testing", "importance": 3, "name": "Jasmine"},
            "karma": {"category": "testing", "importance": 3, "name": "Karma"},
            "enzyme": {"category": "testing", "importance": 3, "name": "Enzyme"},
            "@testing-library/react": {"category": "testing", "importance": 3, "name": "React Testing Library"},
            "cypress": {"category": "testing", "importance": 4, "name": "Cypress"},
            "selenium-webdriver": {"category": "testing", "importance": 3, "name": "Selenium"},
        }
        
        devops_libs = {
            "webpack": {"category": "devops", "importance": 4, "name": "Webpack"},
            "babel": {"category": "devops", "importance": 3, "name": "Babel"},
            "@babel/core": {"category": "devops", "importance": 3, "name": "Babel"},
            "gulp": {"category": "devops", "importance": 3, "name": "Gulp"},
            "grunt": {"category": "devops", "importance": 3, "name": "Grunt"},
            "eslint": {"category": "devops", "importance": 3, "name": "ESLint"},
            "prettier": {"category": "devops", "importance": 3, "name": "Prettier"},
            "typescript": {"category": "language", "importance": 5, "name": "TypeScript"},
            "ts-node": {"category": "devops", "importance": 3, "name": "ts-node"},
            "vite": {"category": "devops", "importance": 4, "name": "Vite"},
        }
        
        all_libs = {
            **frontend_frameworks,
            **backend_frameworks, 
            **database_libs, 
            **testing_libs, 
            **devops_libs
        }
        
        self._add_technology_if_not_exists(result, "language", "JavaScript", 5)
        
        if "typescript" in deps or "ts-node" in deps or "tsc" in package_data.get("scripts", {}):
            self._add_technology_if_not_exists(result, "language", "TypeScript", 5)
        
        for lib, version in deps.items():
            lib_name = lib.split("/")[-1] if lib.startswith("@") else lib
            
            if lib in all_libs:
                lib_info = all_libs[lib]
                self._add_technology_if_not_exists(
                    result,
                    lib_info["category"],
                    lib_info["name"],
                    lib_info["importance"]
                )
            
            if lib in frontend_frameworks or lib_name in frontend_frameworks:
                is_frontend = True
            if lib in backend_frameworks or lib_name in backend_frameworks:
                is_backend = True
        
        if is_frontend and is_backend:
            self._add_technology_if_not_exists(result, "other", "Fullstack JavaScript", 4)
        
        if "react" in deps or "react-dom" in deps:
            self._add_technology_if_not_exists(result, "frontend", "React", 5)
        
        if "react-native" in deps:
            self._add_technology_if_not_exists(result, "framework", "React Native", 5)
        
        scripts = package_data.get("scripts", {})
        if scripts:
            if "build" in scripts and ("react-scripts" in scripts["build"] or "next" in scripts["build"]):
                self._add_technology_if_not_exists(result, "frontend", "React", 5)
            
            if "dev" in scripts and "next" in scripts["dev"]:
                self._add_technology_if_not_exists(result, "frontend", "Next.js", 5)
            
            if "dev" in scripts and "nuxt" in scripts["dev"]:
                self._add_technology_if_not_exists(result, "frontend", "Nuxt.js", 5)
            
            if "start" in scripts and "electron" in scripts["start"]:
                self._add_technology_if_not_exists(result, "framework", "Electron", 4)
    
    def _process_rust_packages(self, package_data: Dict[str, Any], result: Dict[str, List[Any]]) -> None:
        """
        Processes Rust project dependencies and adds the corresponding technologies.
        
        Args:
            package_data: Data from Cargo.toml
            result: Dictionary for accumulating results
        """
        self._add_technology_if_not_exists(result, "language", "Rust", 5)
        
        frameworks = {
            "actix-web": {"category": "backend", "importance": 5, "name": "Actix Web"},
            "rocket": {"category": "backend", "importance": 5, "name": "Rocket"},
            "warp": {"category": "backend", "importance": 4, "name": "Warp"},
            "axum": {"category": "backend", "importance": 4, "name": "Axum"},
            "tide": {"category": "backend", "importance": 4, "name": "Tide"},
            "tokio": {"category": "backend", "importance": 4, "name": "Tokio"},
            "async-std": {"category": "backend", "importance": 4, "name": "async-std"},
            "diesel": {"category": "database", "importance": 4, "name": "Diesel ORM"},
            "sqlx": {"category": "database", "importance": 4, "name": "SQLx"},
            "rusqlite": {"category": "database", "importance": 3, "name": "Rusqlite"},
            "serde": {"category": "other", "importance": 3, "name": "Serde"},
            "reqwest": {"category": "backend", "importance": 3, "name": "Reqwest"},
            "hyper": {"category": "backend", "importance": 3, "name": "Hyper"},
            "clap": {"category": "other", "importance": 3, "name": "Clap CLI"},
            "yew": {"category": "frontend", "importance": 5, "name": "Yew"},
            "leptos": {"category": "frontend", "importance": 5, "name": "Leptos"},
            "dioxus": {"category": "frontend", "importance": 4, "name": "Dioxus"},
            "tauri": {"category": "framework", "importance": 5, "name": "Tauri"},
            "bevy": {"category": "framework", "importance": 5, "name": "Bevy Engine"},
            "amethyst": {"category": "framework", "importance": 4, "name": "Amethyst Engine"},
        }
        
        dependencies = package_data["all_dependencies"]
        for lib_name, lib_version in dependencies.items():
            if lib_name in frameworks:
                lib_info = frameworks[lib_name]
                self._add_technology_if_not_exists(
                    result,
                    lib_info["category"],
                    lib_info["name"],
                    lib_info["importance"]
                )
    
    def _analyze_project_files(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes project files and determines technologies based on their content.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        self._analyze_dotnet_projects(project_path, result)
        
        self._analyze_cpp_projects(project_path, result)
        
        self._analyze_android_projects(project_path, result)
        
        self._analyze_ios_projects(project_path, result)
        
        self._analyze_specific_files(project_path, result)
    
    def _analyze_dotnet_projects(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes .NET projects and determines the technologies used.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        csproj_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(".csproj"):
                    csproj_files.append(os.path.join(root, file))
        
        if csproj_files:
            self._add_technology_if_not_exists(result, "language", "C#", 5)
            self._add_technology_if_not_exists(result, "devops", ".NET", 4)
            
            for csproj_path in csproj_files:
                try:
                    content = self.file_repository.read_file(csproj_path)
                    
                    if "Microsoft.AspNetCore.App" in content or "Microsoft.AspNetCore" in content:
                        self._add_technology_if_not_exists(result, "framework", "ASP.NET Core", 5)
                    
                    if "Microsoft.EntityFrameworkCore" in content:
                        self._add_technology_if_not_exists(result, "database", "Entity Framework Core", 4)
                    
                    if "Microsoft.AspNetCore.Mvc" in content:
                        self._add_technology_if_not_exists(result, "backend", "ASP.NET Core MVC", 4)
                    
                    if "Microsoft.AspNetCore.Components.WebAssembly" in content:
                        self._add_technology_if_not_exists(result, "frontend", "Blazor WebAssembly", 4)
                    elif "Microsoft.AspNetCore.Components.Web" in content:
                        self._add_technology_if_not_exists(result, "frontend", "Blazor", 4)
                    
                    if "xunit" in content.lower():
                        self._add_technology_if_not_exists(result, "testing", "xUnit", 3)
                    if "nunit" in content.lower():
                        self._add_technology_if_not_exists(result, "testing", "NUnit", 3)
                    if "mstest" in content.lower():
                        self._add_technology_if_not_exists(result, "testing", "MSTest", 3)
                except Exception as e:
                    print(f"Error analyzing .csproj file: {e}")
        
        fsproj_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(".fsproj"):
                    fsproj_files.append(os.path.join(root, file))
        
        if fsproj_files:
            self._add_technology_if_not_exists(result, "language", "F#", 5)
            self._add_technology_if_not_exists(result, "devops", ".NET", 4)
        
        vbproj_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(".vbproj"):
                    vbproj_files.append(os.path.join(root, file))
        
        if vbproj_files:
            self._add_technology_if_not_exists(result, "language", "Visual Basic", 5)
            self._add_technology_if_not_exists(result, "devops", ".NET", 4)
    
    def _analyze_cpp_projects(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes C/C++ projects.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        cmake_path = os.path.join(project_path, "CMakeLists.txt")
        if self.file_repository.file_exists(cmake_path):
            self._add_technology_if_not_exists(result, "devops", "CMake", 4)
            
            content = self.file_repository.read_file(cmake_path)
            if "project" in content.lower():
                if "CXX" in content or "CPP" in content:
                    self._add_technology_if_not_exists(result, "language", "C++", 5)
                elif "C" in content and "CXX" not in content and "CPP" not in content:
                    self._add_technology_if_not_exists(result, "language", "C", 5)
        
        makefile_path = os.path.join(project_path, "Makefile")
        if self.file_repository.file_exists(makefile_path):
            self._add_technology_if_not_exists(result, "devops", "Make", 4)
    
    def _analyze_android_projects(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes Android projects.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        manifest_path = os.path.join(project_path, "app", "src", "main", "AndroidManifest.xml")
        gradle_path = os.path.join(project_path, "app", "build.gradle")
        
        if self.file_repository.file_exists(manifest_path):
            self._add_technology_if_not_exists(result, "framework", "Android", 5)
            
            if self.file_repository.file_exists(gradle_path):
                content = self.file_repository.read_file(gradle_path)
                if "kotlin" in content.lower():
                    self._add_technology_if_not_exists(result, "language", "Kotlin", 5)
                else:
                    self._add_technology_if_not_exists(result, "language", "Java", 5)
    
    def _analyze_ios_projects(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes iOS projects.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        xcodeproj_dirs = []
        for root, dirs, _ in os.walk(project_path):
            for dir_name in dirs:
                if dir_name.endswith(".xcodeproj"):
                    xcodeproj_dirs.append(dir_name)
                    break
        
        if xcodeproj_dirs:
            swift_files = []
            objc_files = []
            
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(".swift"):
                        swift_files.append(os.path.join(root, file))
                    elif file.endswith(".m") or file.endswith(".h"):
                        objc_files.append(os.path.join(root, file))
            
            if swift_files:
                self._add_technology_if_not_exists(result, "language", "Swift", 5)
                self._add_technology_if_not_exists(result, "framework", "iOS", 5)
            elif objc_files:
                self._add_technology_if_not_exists(result, "language", "Objective-C", 5)
                self._add_technology_if_not_exists(result, "framework", "iOS", 5)
    
    def _analyze_specific_files(self, project_path: str, result: Dict[str, List[Any]]) -> None:
        """
        Analyzes specific files to determine additional technologies.
        
        Args:
            project_path: The path to the project root
            result: Dictionary for accumulating results
        """
        project_files_config = self.config_repository.get_config("analyzers.project_files")
        
        for filename, technology in project_files_config.items():
            file_path = os.path.join(project_path, filename)
            if self.file_repository.file_exists(file_path):
                category = self._determine_technology_category(technology)
                self._add_technology_if_not_exists(result, category, technology, 3)
    
    def _determine_technology_category(self, technology: str) -> str:
        """
        Determines the category for a technology.
        
        Args:
            technology: The name of the technology
            
        Returns:
            str: The category of the technology
        """
        frontend_techs = ['Angular', 'React', 'Vue.js', 'Next.js', 'Gatsby', 'Svelte', 'HTML', 'CSS', 'SASS', 'LESS', 'Bootstrap', 'Tailwind', 'Blazor WebAssembly']
        backend_techs = ['Express', 'Django', 'Flask', 'FastAPI', 'Spring', 'ASP.NET Core', 'Laravel', 'Rails']
        database_techs = ['MongoDB', 'MySQL', 'PostgreSQL', 'SQLite', 'Redis', 'Entity Framework', 'Hibernate', 'SQL Server']
        devops_techs = ['Docker', 'Kubernetes', 'Travis CI', 'Jenkins', 'GitHub Actions', 'GitLab CI', 'Terraform', 'Ansible', 'AWS', 'Azure', 'GCP']
        testing_techs = ['Jest', 'Mocha', 'Cypress', 'Selenium', 'JUnit', 'xUnit', 'NUnit', 'PyTest']
        framework_techs = ['Android', 'iOS', '.NET Core', 'Spring Boot', 'ASP.NET Core', 'Flutter', 'React Native']
        
        technology_lower = technology.lower()
        
        if any(tech.lower() in technology_lower for tech in frontend_techs):
            return "frontend"
        elif any(tech.lower() in technology_lower for tech in backend_techs):
            return "backend"
        elif any(tech.lower() in technology_lower for tech in database_techs):
            return "database"
        elif any(tech.lower() in technology_lower for tech in devops_techs):
            return "devops"
        elif any(tech.lower() in technology_lower for tech in testing_techs):
            return "testing"
        elif any(tech.lower() in technology_lower for tech in framework_techs):
            return "framework"
        else:
            return "other"
    
    def _add_technology_if_not_exists(self, result: Dict[str, List[Any]], category: str, name: str, importance: int) -> None:
        """
        Adds a technology to the result if it does not exist.
        
        Args:
            result: Dictionary for accumulating results
            category: The category of the technology
            name: The name of the technology
            importance: The importance of the technology (1-5)
        """
        if category not in result:
            result[category] = []
        
        for tech in result[category]:
            if isinstance(tech, dict) and tech.get("name") == name:
                if tech.get("importance", 0) < importance:
                    tech["importance"] = importance
                return
        
        result[category].append({
            "name": name,
            "importance": importance
        })

    def _parse_pom_xml(self, path: str) -> List[Dict[str, str]]:
        """
        Parses the pom.xml file and returns a list of dependencies.
        
        Args:
            path: The path to the pom.xml file
            
        Returns:
            List[Dict[str, str]]: List of dependencies with their group, artifact, and version
        """
        dependencies = []
        try:
            content = self.file_repository.read_file(path)
            
            dependency_pattern = r'<dependency>(.+?)</dependency>'
            group_pattern = r'<groupId>(.+?)</groupId>'
            artifact_pattern = r'<artifactId>(.+?)</artifactId>'
            version_pattern = r'<version>(.+?)</version>'
            
            for match in re.finditer(dependency_pattern, content, re.DOTALL):
                dep_content = match.group(1)
                
                group_match = re.search(group_pattern, dep_content)
                artifact_match = re.search(artifact_pattern, dep_content)
                version_match = re.search(version_pattern, dep_content)
                
                group = group_match.group(1) if group_match else ""
                artifact = artifact_match.group(1) if artifact_match else ""
                version = version_match.group(1) if version_match else ""
                
                dependencies.append({
                    "group": group,
                    "artifact": artifact,
                    "version": version,
                    "name": f"{group}:{artifact}"
                })
            
            parent_pattern = r'<parent>(.+?)</parent>'
            for match in re.finditer(parent_pattern, content, re.DOTALL):
                parent_content = match.group(1)
                group_match = re.search(group_pattern, parent_content)
                artifact_match = re.search(artifact_pattern, parent_content)
                
                group = group_match.group(1) if group_match else ""
                artifact = artifact_match.group(1) if artifact_match else ""
                
                if "org.springframework.boot" in group and "spring-boot-starter-parent" in artifact:
                    dependencies.append({
                        "group": "org.springframework.boot",
                        "artifact": "spring-boot-starter-parent",
                        "version": "",
                        "name": "Spring Boot"
                    })
        except Exception as e:
            print(f"Error parsing pom.xml: {e}")
        
        return dependencies
    
    def _process_java_packages(self, dependencies: List[Dict[str, str]], result: Dict[str, List[Any]]) -> None:
        """
        Processes Java project dependencies and adds technologies to the result.
        
        Args:
            dependencies: List of dependencies
            result: Dictionary for accumulating results
        """
        self._add_technology_if_not_exists(result, "language", "Java", 5)
        
        framework_map = {
            "org.springframework.boot": {"category": "framework", "importance": 5, "name": "Spring Boot"},
            "org.springframework": {"category": "framework", "importance": 5, "name": "Spring Framework"},
            "jakarta.servlet": {"category": "framework", "importance": 4, "name": "Jakarta EE"},
            "javax.servlet": {"category": "framework", "importance": 4, "name": "Java EE"},
            "org.hibernate": {"category": "database", "importance": 4, "name": "Hibernate"},
            "javax.persistence": {"category": "database", "importance": 4, "name": "JPA"},
            "jakarta.persistence": {"category": "database", "importance": 4, "name": "JPA"},
            "org.mybatis": {"category": "database", "importance": 4, "name": "MyBatis"},
            "mysql": {"category": "database", "importance": 3, "name": "MySQL"},
            "org.postgresql": {"category": "database", "importance": 3, "name": "PostgreSQL"},
            "com.h2database": {"category": "database", "importance": 3, "name": "H2 Database"},
            "org.junit": {"category": "testing", "importance": 3, "name": "JUnit"},
            "org.mockito": {"category": "testing", "importance": 3, "name": "Mockito"},
            "org.testng": {"category": "testing", "importance": 3, "name": "TestNG"},
            "io.cucumber": {"category": "testing", "importance": 3, "name": "Cucumber"},
            "org.seleniumhq.selenium": {"category": "testing", "importance": 3, "name": "Selenium"},
            "com.squareup.retrofit2": {"category": "backend", "importance": 3, "name": "Retrofit"},
            "com.squareup.okhttp3": {"category": "backend", "importance": 3, "name": "OkHttp"},
            "io.micronaut": {"category": "framework", "importance": 5, "name": "Micronaut"},
            "io.quarkus": {"category": "framework", "importance": 5, "name": "Quarkus"},
            "io.vertx": {"category": "framework", "importance": 4, "name": "Vert.x"}
        }
        
        spring_boot_starters = {
            "spring-boot-starter-web": {"category": "backend", "importance": 4, "name": "Spring MVC"},
            "spring-boot-starter-webflux": {"category": "backend", "importance": 4, "name": "Spring WebFlux"},
            "spring-boot-starter-data-jpa": {"category": "database", "importance": 4, "name": "Spring Data JPA"},
            "spring-boot-starter-data-mongodb": {"category": "database", "importance": 4, "name": "Spring Data MongoDB"},
            "spring-boot-starter-data-redis": {"category": "database", "importance": 4, "name": "Spring Data Redis"},
            "spring-boot-starter-security": {"category": "backend", "importance": 4, "name": "Spring Security"},
            "spring-boot-starter-test": {"category": "testing", "importance": 3, "name": "Spring Testing"},
            "spring-boot-starter-actuator": {"category": "devops", "importance": 3, "name": "Spring Actuator"},
            "spring-boot-starter-thymeleaf": {"category": "frontend", "importance": 4, "name": "Thymeleaf"},
            "spring-boot-starter-freemarker": {"category": "frontend", "importance": 4, "name": "FreeMarker"}
        }
        
        for dependency in dependencies:
            group = dependency["group"]
            artifact = dependency["artifact"]
            
            if group == "org.springframework.boot" and artifact.startswith("spring-boot-starter"):
                if artifact in spring_boot_starters:
                    starter_info = spring_boot_starters[artifact]
                    self._add_technology_if_not_exists(
                        result, 
                        starter_info["category"],
                        starter_info["name"],
                        starter_info["importance"]
                    )
                continue
            
            for lib_prefix, lib_info in framework_map.items():
                if group.startswith(lib_prefix):
                    self._add_technology_if_not_exists(
                        result,
                        lib_info["category"],
                        lib_info["name"],
                        lib_info["importance"]
                    )
                    break


def _is_ignored_dir(path: str) -> bool:
    """
    Checks if a directory should be ignored.
    
    Args:
        path: The path to the directory
        
    Returns:
        bool: True, if the directory should be ignored
    """
    ignored_dirs = [
        '.git', '.github', '.vscode', '.idea', '.vs', 
        'node_modules', '__pycache__', 'venv', 'env',
        'dist', 'build', 'target', 'bin', 'obj', 
        '.pytest_cache', '.coverage', '.next', 'coverage',
        '.nuget', 'packages', '.gradle'
    ]
    
    for ignored in ignored_dirs:
        if ignored in path.split(os.sep):
            return True
    return False


def _is_ignored_file(filename: str) -> bool:
    """
    Checks if a file should be ignored.
    
    Args:
        filename: The name of the file
        
    Returns:
        bool: True, if the file should be ignored
    """
    ignored_patterns = [
        '.gitignore', '.gitattributes', '.DS_Store', 'Thumbs.db',
        '.env', '.env.local', '.env.development', '.env.test', '.env.production',
        '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.obj', '*.o',
        '*.a', '*.lib', '*.egg', '*.egg-info', '*.whl', '*.pdb', '*.cache',
        '*.class', '*.jar', '*.war', '*.ear', '*.zip', '*.tar.gz', '*.rar'
    ]
    
    for pattern in ignored_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False