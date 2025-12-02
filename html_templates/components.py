"""HTML components for report generation."""

from html import escape as html_escape
from typing import Dict, List, Optional


def render_header(
    report_type: str,
    total_titles: int,
    hot_news_count: int,
    generated_time: str,
) -> str:
    """Render the header section of the HTML report.

    Args:
        report_type: Type of report (当日汇总, 实时分析, etc.)
        total_titles: Total number of news titles
        hot_news_count: Number of hot news items
        generated_time: Formatted generation time string

    Returns:
        HTML string for the header section
    """
    return f"""
            <div class="header">
                <div class="save-buttons">
                    <button class="save-btn" onclick="saveAsImage()">保存为图片</button>
                    <button class="save-btn" onclick="saveAsMultipleImages()">分段保存</button>
                </div>
                <div class="header-title">热点新闻分析</div>
                <div class="header-info">
                    <div class="info-item">
                        <span class="info-label">报告类型</span>
                        <span class="info-value">{report_type}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">新闻总数</span>
                        <span class="info-value">{total_titles} 条</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">热点新闻</span>
                        <span class="info-value">{hot_news_count} 条</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">生成时间</span>
                        <span class="info-value">{generated_time}</span>
                    </div>
                </div>
            </div>"""


def render_error_section(failed_ids: List[str]) -> str:
    """Render the error section for failed platform requests.

    Args:
        failed_ids: List of failed platform IDs

    Returns:
        HTML string for the error section
    """
    if not failed_ids:
        return ""

    error_items = "".join(
        f'<li class="error-item">{html_escape(id_value)}</li>'
        for id_value in failed_ids
    )

    return f"""
                <div class="error-section">
                    <div class="error-title">⚠️ 请求失败的平台</div>
                    <ul class="error-list">{error_items}
                    </ul>
                </div>"""


def _get_heat_class(count: int) -> str:
    """Get the CSS class based on heat level.

    Args:
        count: Number of news items

    Returns:
        CSS class name (hot, warm, or empty string)
    """
    if count >= 10:
        return "hot"
    elif count >= 5:
        return "warm"
    return ""


def _get_rank_class(min_rank: int, rank_threshold: int = 10) -> str:
    """Get the CSS class based on rank.

    Args:
        min_rank: Minimum rank value
        rank_threshold: Threshold for high rank

    Returns:
        CSS class name (top, high, or empty string)
    """
    if min_rank <= 3:
        return "top"
    elif min_rank <= rank_threshold:
        return "high"
    return ""


def _format_rank_text(ranks: List[int]) -> str:
    """Format rank display text.

    Args:
        ranks: List of rank values

    Returns:
        Formatted rank string
    """
    if not ranks:
        return ""
    min_rank = min(ranks)
    max_rank = max(ranks)
    if min_rank == max_rank:
        return str(min_rank)
    return f"{min_rank}-{max_rank}"


def render_news_item(
    index: int,
    title_data: Dict,
) -> str:
    """Render a single news item.

    Args:
        index: Item index (1-based)
        title_data: Dictionary containing news item data

    Returns:
        HTML string for the news item
    """
    is_new = title_data.get("is_new", False)
    new_class = "new" if is_new else ""

    html = f"""
                    <div class="news-item {new_class}">
                        <div class="news-number">{index}</div>
                        <div class="news-content">
                            <div class="news-header">
                                <span class="source-name">{html_escape(title_data["source_name"])}</span>"""

    # Process rank display
    ranks = title_data.get("ranks", [])
    if ranks:
        min_rank = min(ranks)
        rank_threshold = title_data.get("rank_threshold", 10)
        rank_class = _get_rank_class(min_rank, rank_threshold)
        rank_text = _format_rank_text(ranks)
        html += f'<span class="rank-num {rank_class}">{rank_text}</span>'

    # Process time display
    time_display = title_data.get("time_display", "")
    if time_display:
        simplified_time = (
            time_display.replace(" ~ ", "~")
            .replace("[", "")
            .replace("]", "")
        )
        html += f'<span class="time-info">{html_escape(simplified_time)}</span>'

    # Process count
    count_info = title_data.get("count", 1)
    if count_info > 1:
        html += f'<span class="count-info">{count_info}次</span>'

    html += """
                            </div>
                            <div class="news-title">"""

    # Process title and link
    escaped_title = html_escape(title_data["title"])
    link_url = title_data.get("mobile_url") or title_data.get("url", "")

    if link_url:
        escaped_url = html_escape(link_url)
        html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
    else:
        html += escaped_title

    html += """
                            </div>
                        </div>
                    </div>"""

    return html


def render_word_group(
    stat: Dict,
    index: int,
    total_count: int,
) -> str:
    """Render a word group with its news items.

    Args:
        stat: Dictionary containing word statistics and news items
        index: Group index (1-based)
        total_count: Total number of word groups

    Returns:
        HTML string for the word group
    """
    count = stat["count"]
    count_class = _get_heat_class(count)
    escaped_word = html_escape(stat["word"])

    html = f"""
                <div class="word-group">
                    <div class="word-header" onclick="toggleAccordion(this)">
                        <div class="word-info">
                            <div class="word-name">{escaped_word}</div>
                            <div class="word-count {count_class}">{count} 条</div>
                        </div>
                        <div style="display: flex; align-items: center;">
                            <div class="word-index">{index}/{total_count}</div>
                            <span class="toggle-icon">▼</span>
                        </div>
                    </div>
                    <div class="news-list">"""

    # Render each news item
    for j, title_data in enumerate(stat["titles"], 1):
        html += render_news_item(j, title_data)

    html += """
                    </div>
                </div>"""

    return html


def render_new_item(
    index: int,
    title_data: Dict,
) -> str:
    """Render a single new item in the new section.

    Args:
        index: Item index (1-based)
        title_data: Dictionary containing news item data

    Returns:
        HTML string for the new item
    """
    ranks = title_data.get("ranks", [])

    if ranks:
        min_rank = min(ranks)
        rank_class = _get_rank_class(min_rank, title_data.get("rank_threshold", 10))
        rank_text = _format_rank_text(ranks)
    else:
        rank_class = ""
        rank_text = "?"

    escaped_title = html_escape(title_data["title"])
    link_url = title_data.get("mobile_url") or title_data.get("url", "")

    title_html = (
        f'<a href="{html_escape(link_url)}" target="_blank" class="news-link">{escaped_title}</a>'
        if link_url
        else escaped_title
    )

    return f"""
                        <div class="new-item">
                            <div class="new-item-number">{index}</div>
                            <div class="new-item-rank {rank_class}">{rank_text}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">{title_html}
                                </div>
                            </div>
                        </div>"""


def render_new_section(new_titles: List[Dict], total_new_count: int) -> str:
    """Render the new titles section.

    Args:
        new_titles: List of new title data grouped by source
        total_new_count: Total count of new titles

    Returns:
        HTML string for the new section
    """
    if not new_titles:
        return ""

    html = f"""
                <div class="new-section">
                    <div class="new-section-title">本次新增热点 (共 {total_new_count} 条)</div>"""

    for source_data in new_titles:
        escaped_source = html_escape(source_data["source_name"])
        titles_count = len(source_data["titles"])

        html += f"""
                    <div class="new-source-group">
                        <div class="new-source-title">{escaped_source} · {titles_count}条</div>"""

        for idx, title_data in enumerate(source_data["titles"], 1):
            html += render_new_item(idx, title_data)

        html += """
                    </div>"""

    html += """
                </div>"""

    return html


def render_footer(update_info: Optional[Dict] = None) -> str:
    """Render the footer section.

    Args:
        update_info: Optional dictionary with version update information

    Returns:
        HTML string for the footer section
    """
    html = """
            <div class="footer">
                <div class="footer-content">
                    由 <span class="project-name">TrendRadar</span> 生成 ·
                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" class="footer-link">
                        GitHub 开源项目
                    </a>"""

    if update_info:
        html += f"""
                    <br>
                    <span style="color: #ea580c; font-weight: 500;">
                        发现新版本 {update_info['remote_version']}，当前版本 {update_info['current_version']}
                    </span>"""

    html += """
                </div>
            </div>"""

    return html
