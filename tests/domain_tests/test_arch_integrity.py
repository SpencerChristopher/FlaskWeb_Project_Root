import ast
import os
from pathlib import Path
import pytest

# Define the root of the source code
SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src"

def get_imports_from_file(file_path):
    """Parses a python file and returns a list of all imported modules."""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
        except Exception:
            return []
            
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def get_all_python_files(directory):
    """Recursively finds all .py files in a directory."""
    return list(Path(directory).rglob("*.py"))

@pytest.mark.design
class TestArchIntegrity:
    """
    Automated Architectural Integrity Gate.
    Verifies that the code adheres to the boundaries defined in ARCHITECTURE.md.
    """

    def test_repository_isolation(self):
        """
        G1: Repositories must be isolated.
        They must NOT import from Services or Routes.
        """
        repo_dir = SRC_ROOT / "repositories"
        files = get_all_python_files(repo_dir)
        
        forbidden_patterns = ["src.services", "src.routes", "src.app"]
        
        violations = []
        for file in files:
            imports = get_imports_from_file(file)
            for imp in imports:
                if any(imp.startswith(p) for p in forbidden_patterns):
                    violations.append(f"{file.relative_to(SRC_ROOT)}: imports {imp}")
        
        assert not violations, f"Repository Isolation Violation detected:\n" + "\n".join(violations)

    def test_service_layer_purity(self):
        """
        G2: Services must be independent of the Transport layer.
        They must NOT import from Routes or the Flask App directly.
        """
        service_dir = SRC_ROOT / "services"
        files = get_all_python_files(service_dir)
        
        forbidden_patterns = ["src.routes", "src.app.routes"]
        
        violations = []
        for file in files:
            imports = get_imports_from_file(file)
            for imp in imports:
                if any(imp.startswith(p) for p in forbidden_patterns):
                    violations.append(f"{file.relative_to(SRC_ROOT)}: imports {imp}")
        
        assert not violations, f"Service Layer Purity Violation detected:\n" + "\n".join(violations)

    def test_no_circular_dependencies_core(self):
        """
        G3: Ensure core modules don't import the app factory.
        Prevents circular dependencies during bootstrap.
        """
        core_files = list(SRC_ROOT.glob("*.py"))
        
        forbidden = "src.server"
        
        violations = []
        for file in core_files:
            if file.name == "server.py": continue
            imports = get_imports_from_file(file)
            if any(imp == forbidden for imp in imports):
                violations.append(f"{file.name}: imports {forbidden}")
                
        assert not violations, f"Circular Dependency Risk detected:\n" + "\n".join(violations)
