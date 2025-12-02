"""HTML templates module for TrendRadar report generation."""

from .styles import get_html_styles
from .scripts import get_html_scripts
from .components import (
    render_header,
    render_error_section,
    render_word_group,
    render_news_item,
    render_new_section,
    render_footer,
)

__all__ = [
    "get_html_styles",
    "get_html_scripts",
    "render_header",
    "render_error_section",
    "render_word_group",
    "render_news_item",
    "render_new_section",
    "render_footer",
]
