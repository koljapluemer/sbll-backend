"""
CMS Views Package

This package organizes views by model/feature:
- home: Home page redirect
- language: Language CRUD operations
- gloss: Gloss CRUD operations
- situation: Situation CRUD operations
- api: API endpoints for AJAX operations
- shared: Shared utility functions
"""

from .home import redirect_home

# Language views
from .language import (
    language_list,
    language_create,
    language_update,
    language_delete,
)

# Gloss views
from .gloss import (
    gloss_list,
    gloss_create,
    gloss_update,
    gloss_delete,
)

# Situation views
from .situation import (
    situation_list,
    situation_create,
    situation_update,
    situation_delete,
    situation_download_all,
)

# API views
from .api import (
    api_gloss_search,
    api_gloss_create,
    api_gloss_create_or_get,
)

# AI views
from .ai import gloss_tools, gloss_variations

# Tools views
from .tools import (
    tools_list,
    tools_untranslated_glosses,
    tools_translate_glosses,
)

__all__ = [
    # Home
    "redirect_home",
    # Language
    "language_list",
    "language_create",
    "language_update",
    "language_delete",
    # Gloss
    "gloss_list",
    "gloss_create",
    "gloss_update",
    "gloss_delete",
    # Situation
    "situation_list",
    "situation_create",
    "situation_update",
    "situation_delete",
    "situation_download_all",
    # API
    "api_gloss_search",
    "api_gloss_create",
    "api_gloss_create_or_get",
    # AI
    "gloss_tools",
    "gloss_variations",
    # Tools
    "tools_list",
    "tools_untranslated_glosses",
    "tools_translate_glosses",
]
