"""Shared Sphinx configuration for English and Japanese documentation."""
from pathlib import Path
import sys

DOCS_DIR = Path(__file__).resolve().parent
ROOT_DIR = DOCS_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

project = "n10w02"
master_doc = "index"
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_mock_imports = ["win32com", "pythoncom"]
html_theme = "sphinx_rtd_theme"
html_theme_options = {"collapse_navigation": False, "navigation_depth": 4}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
