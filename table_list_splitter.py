"""Advanced chunking for tables and lists."""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


class TableListSplitter:
    """Handles splitting of long tables and lists into manageable chunks."""
    
    def __init__(
        self,
        items_per_chunk: int = 12,
        rows_per_chunk: int = 8,
        groups_per_chunk: int = 8,
        min_long_list: int = 25,
        min_long_table: int = 15,
        min_nested_groups: int = 5,
        min_nested_items: int = 12,
        debug_mode: bool = False
    ):
        """
        Initialize the splitter.
        
        Args:
            items_per_chunk: List items per chunk.
            rows_per_chunk: Table rows per chunk.
            groups_per_chunk: Nested bullet groups per chunk.
            min_long_list: Minimum items to trigger list splitting.
            min_long_table: Minimum rows to trigger table splitting.
            min_nested_groups: Minimum groups for nested bullet detection.
            min_nested_items: Minimum nested items for detection.
            debug_mode: Enable verbose logging.
        """
        self.items_per_chunk = items_per_chunk
        self.rows_per_chunk = rows_per_chunk
        self.groups_per_chunk = groups_per_chunk
        self.min_long_list = min_long_list
        self.min_long_table = min_long_table
        self.min_nested_groups = min_nested_groups
        self.min_nested_items = min_nested_items
        self.debug_mode = debug_mode
    
    def detect_long_list(self, text: str) -> bool:
        """
        Check if text contains a long list (25+ main items by default).
        
        Only counts top-level items, not nested sub-items.
        Will not detect nested bullet tables.
        
        Args:
            text: Markdown text to analyze.
            
        Returns:
            True if long list detected.
        """
        lines = text.split('\n')
        main_item_count = 0
        has_nested_structure = False
        
        # Check if this is actually a nested bullet table
        for i, line in enumerate(lines):
            if re.match(r'^\*\s+', line) and not re.match(r'^\s+', line):
                # Check if next non-empty line is nested
                for j in range(i + 1, min(i + 5, len(lines))):
                    if re.match(r'^\s{2,}\*\s+', lines[j]):
                        has_nested_structure = True
                        break
                    elif lines[j].strip() and not re.match(r'^\*\s+', lines[j]):
                        break
            
            if has_nested_structure:
                break
        
        # Don't treat nested structures as simple lists
        if has_nested_structure:
            return False
        
        # Count only top-level items
        for line in lines:
            if re.match(r'^[*\-+]\s+\w', line) or re.match(r'^\d+\.\s+\w', line):
                main_item_count += 1
        
        if main_item_count >= self.min_long_list:
            logger.info(
                f"Long list detected: {main_item_count} items "
                f"(threshold: {self.min_long_list})"
            )
        
        return main_item_count >= self.min_long_list
    
    def detect_long_table(self, text: str) -> bool:
        """
        Check if text contains a long markdown table (15+ rows by default).
        
        Args:
            text: Markdown text to analyze.
            
        Returns:
            True if long table detected.
        """
        lines = text.split('\n')
        table_row_count = 0
        
        for line in lines:
            stripped = line.strip()
            # Count lines starting with | but not separator lines
            if stripped.startswith('|') and not re.match(r'^\|[\s\-:]+\|', stripped):
                table_row_count += 1
        
        # Subtract header row
        if table_row_count > 1:
            table_row_count -= 1
        
        if table_row_count >= self.min_long_table:
            logger.info(
                f"Long table detected: {table_row_count} rows "
                f"(threshold: {self.min_long_table})"
            )
        
        return table_row_count >= self.min_long_table
    
    def detect_nested_bullet_table(self, text: str) -> bool:
        """
        Check if text contains nested bullet points representing tabular data.
        
        Example:
        * Main item 1
          * Sub-item 1.1
          * Sub-item 1.2
        * Main item 2
          * Sub-item 2.1
        
        Args:
            text: Markdown text to analyze.
            
        Returns:
            True if nested bullet table detected.
        """
        # Remove continuation markers
        text = re.sub(
            r'\*\*\[Part \d+ of \d+(?:\s+-\s+Continued)?\]\*\*',
            '',
            text
        )
        
        lines = text.split('\n')
        group_count = 0
        total_nested_count = 0
        in_group = False
        has_nested = False
        
        for line in lines:
            # Main bullet (not indented)
            if (re.match(r'^\*\s+\w', line) or re.match(r'^\*\s+\[', line)) and \
               not re.match(r'^\s+', line):
                if in_group and has_nested:
                    group_count += 1
                in_group = True
                has_nested = False
            # Nested bullet (indented)
            elif re.match(r'^\s{2,}\*\s+', line) and in_group:
                has_nested = True
                total_nested_count += 1
        
        # Count last group
        if in_group and has_nested:
            group_count += 1
        
        # Detection criteria
        detected_by_groups = group_count >= self.min_nested_groups
        detected_by_nested = total_nested_count >= self.min_nested_items
        
        if detected_by_groups or detected_by_nested:
            reasons = []
            if detected_by_groups:
                reasons.append(
                    f"{group_count} groups (threshold: {self.min_nested_groups})"
                )
            if detected_by_nested:
                reasons.append(
                    f"{total_nested_count} nested items "
                    f"(threshold: {self.min_nested_items})"
                )
            
            logger.info(f"Nested bullet table detected: {' and '.join(reasons)}")
            return True
        
        return False
    
    def split_long_list(self, text: str, guide_title: str = "") -> List[str]:
        """
        Split long list into smaller chunks with preserved context.
        
        Each chunk includes the heading and list context prepended.
        Handles nested bullet points (main item + sub-items).
        
        Args:
            text: Markdown text containing the list.
            guide_title: Guide title for context.
            
        Returns:
            List of text chunks with context preserved.
        """
        lines = text.split('\n')
        
        # Extract heading and preamble
        heading_lines = []
        list_start_idx = None
        
        for i, line in enumerate(lines):
            if list_start_idx is None and \
               (re.match(r'^[*\-+]\s+\w', line) or re.match(r'^\d+\.\s+\w', line)):
                list_start_idx = i
                break
            else:
                heading_lines.append(line)
        
        if list_start_idx is None:
            return [text]
        
        heading_text = '\n'.join(heading_lines).strip()
        
        # Extract list items with nested content
        list_items = []
        current_item = []
        
        for i in range(list_start_idx, len(lines)):
            line = lines[i]
            
            # New main item
            if re.match(r'^[*\-+]\s+\w', line) or re.match(r'^\d+\.\s+\w', line):
                if current_item:
                    list_items.append('\n'.join(current_item))
                current_item = [line]
            elif current_item:
                # Continuation (nested bullets, indented text)
                current_item.append(line)
        
        # Add last item
        if current_item:
            list_items.append('\n'.join(current_item))
        
        if not list_items:
            return [text]
        
        logger.info(
            f"Splitting {len(list_items)} items into chunks of "
            f"{self.items_per_chunk}"
        )
        
        if self.debug_mode and list_items:
            preview = list_items[0][:100].replace('\n', ' ')
            logger.debug(f"First item: {preview}...")
        
        # Split into chunks
        chunks = []
        for i in range(0, len(list_items), self.items_per_chunk):
            chunk_items = list_items[i:i + self.items_per_chunk]
            chunk_end = min(i + self.items_per_chunk, len(list_items))
            
            chunk_parts = []
            if heading_text:
                chunk_parts.append(heading_text)
            
            # Add context note
            if i > 0:
                part_num = (i // self.items_per_chunk) + 1
                chunk_parts.append(
                    f"\n**[Part {part_num}: Items {i+1}-{chunk_end} "
                    f"of {len(list_items)} total]**\n"
                )
            else:
                chunk_parts.append(
                    f"\n**[Part 1: Items 1-{chunk_end} "
                    f"of {len(list_items)} total]**\n"
                )
            
            chunk_parts.append('\n'.join(chunk_items))
            
            result_chunk = '\n\n'.join(chunk_parts)
            chunks.append(result_chunk)
            
            if self.debug_mode:
                first_line = chunk_items[0].split('\n')[0][:80]
                logger.debug(
                    f"  Chunk {len(chunks)}: {len(chunk_items)} items, "
                    f"{len(result_chunk)} chars | First: {first_line}..."
                )
        
        return chunks
    
    def split_long_table(self, text: str, guide_title: str = "") -> List[str]:
        """
        Split long markdown table into smaller chunks with preserved context.
        
        Each chunk includes heading, table header, and separator line.
        
        Args:
            text: Markdown text containing the table.
            guide_title: Guide title for context.
            
        Returns:
            List of text chunks with context preserved.
        """
        lines = text.split('\n')
        
        # Extract heading and preamble
        heading_lines = []
        table_start_idx = None
        table_name = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if table_start_idx is None and stripped.startswith('|'):
                table_start_idx = i
                
                # Try to extract table name from line before table
                if heading_lines:
                    last_line = heading_lines[-1].strip()
                    if last_line.startswith('#'):
                        table_name = last_line.lstrip('#').strip()
                    elif last_line.startswith('**') and last_line.endswith('**'):
                        table_name = last_line.strip('*').strip()
                    elif last_line:
                        table_name = last_line
                break
            else:
                heading_lines.append(line)
        
        if table_start_idx is None:
            return [text]
        
        heading_text = '\n'.join(heading_lines).strip()
        
        # Extract table components
        table_header = None
        table_separator = None
        table_rows = []
        
        for i in range(table_start_idx, len(lines)):
            line = lines[i].strip()
            
            if not line.startswith('|'):
                break
            
            # Separator line
            if re.match(r'^\|[\s\-:]+\|', line):
                table_separator = line
                continue
            
            # First row is header
            if table_header is None:
                table_header = line
            else:
                table_rows.append(line)
        
        if not table_rows or table_header is None:
            return [text]
        
        table_name_display = f" for '{table_name}'" if table_name else ""
        logger.info(
            f"Splitting table{table_name_display} with {len(table_rows)} rows "
            f"into chunks of {self.rows_per_chunk}"
        )
        
        # Split into chunks
        chunks = []
        for i in range(0, len(table_rows), self.rows_per_chunk):
            chunk_rows = table_rows[i:i + self.rows_per_chunk]
            chunk_end = min(i + self.rows_per_chunk, len(table_rows))
            
            chunk_parts = []
            if heading_text:
                chunk_parts.append(heading_text)
            
            # Add context note
            table_context = f" - {table_name}" if table_name else ""
            if i > 0:
                part_num = (i // self.rows_per_chunk) + 1
                chunk_parts.append(
                    f"\n**[Part {part_num}: Rows {i+1}-{chunk_end} "
                    f"of {len(table_rows)} total{table_context}]**\n"
                )
            else:
                chunk_parts.append(
                    f"\n**[Part 1: Rows 1-{chunk_end} "
                    f"of {len(table_rows)} total{table_context}]**\n"
                )
            
            # Build table for this chunk
            table_lines = [table_header]
            if table_separator:
                table_lines.append(table_separator)
            table_lines.extend(chunk_rows)
            
            chunk_parts.append('\n'.join(table_lines))
            
            result_chunk = '\n\n'.join(chunk_parts)
            chunks.append(result_chunk)
            
            if self.debug_mode:
                first_row = chunk_rows[0][:80] if chunk_rows else ""
                logger.debug(
                    f"  Chunk {len(chunks)}: {len(chunk_rows)} rows, "
                    f"{len(result_chunk)} chars | First: {first_row}..."
                )
        
        return chunks
    
    def split_nested_bullet_table(self, text: str, guide_title: str = "") -> List[str]:
        """
        Split nested bullet point tables into smaller chunks.
        
        Each main bullet with its nested items is treated as one group.
        
        Args:
            text: Markdown text containing nested bullet table.
            guide_title: Guide title for context.
            
        Returns:
            List of text chunks with context preserved.
        """
        lines = text.split('\n')
        
        # Extract heading and preamble
        heading_lines = []
        nested_start_idx = None
        table_name = None
        
        for i, line in enumerate(lines):
            # Skip continuation markers
            if re.match(
                r'\*\*\[Part \d+ of \d+(?:\s+-\s+Continued)?\]\*\*',
                line.strip()
            ):
                continue
            
            # Look for main bullet followed by nested bullets
            if nested_start_idx is None:
                if re.match(r'^\*\s+\w', line) or re.match(r'^\*\s+\[', line):
                    # Check if next line is nested
                    has_nested = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if re.match(r'^\s{2,}\*\s+', lines[j]):
                            has_nested = True
                            break
                        elif lines[j].strip() and \
                             not re.match(r'^\*\s+', lines[j]) and \
                             not re.match(r'^\s+', lines[j]):
                            break
                    
                    if has_nested:
                        nested_start_idx = i
                        # Try to extract table name
                        if heading_lines:
                            last = heading_lines[-1].strip()
                            if last.startswith('#'):
                                table_name = last.lstrip('#').strip()
                            elif last.startswith('**') and last.endswith('**'):
                                table_name = last.strip('*').strip()
                        break
                
                heading_lines.append(line)
            else:
                break
        
        if nested_start_idx is None:
            return [text]
        
        heading_text = '\n'.join(heading_lines).strip()
        
        # Extract groups
        groups = []
        current_group = []
        
        for i in range(nested_start_idx, len(lines)):
            line = lines[i]
            
            # Skip continuation markers
            if re.match(
                r'\*\*\[Part \d+ of \d+(?:\s+-\s+Continued)?\]\*\*',
                line.strip()
            ):
                continue
            
            # New main bullet
            if (re.match(r'^\*\s+\w', line) or re.match(r'^\*\s+\[', line)) and \
               not re.match(r'^\s+', line):
                if current_group:
                    groups.append('\n'.join(current_group))
                current_group = [line]
            elif current_group and \
                 (re.match(r'^\s+\*\s+', line) or (not line.strip())):
                current_group.append(line)
            elif current_group and line.strip():
                # End of nested structure
                break
        
        # Add last group
        if current_group:
            groups.append('\n'.join(current_group))
        
        if not groups:
            return [text]
        
        table_name_display = f" '{table_name}'" if table_name else ""
        logger.info(
            f"Splitting nested bullet table{table_name_display} with "
            f"{len(groups)} groups into chunks of {self.groups_per_chunk}"
        )
        
        # Split into chunks
        chunks = []
        for i in range(0, len(groups), self.groups_per_chunk):
            chunk_groups = groups[i:i + self.groups_per_chunk]
            chunk_end = min(i + self.groups_per_chunk, len(groups))
            
            chunk_parts = []
            if heading_text:
                chunk_parts.append(heading_text)
            
            # Add context note
            table_context = f" - {table_name}" if table_name else ""
            if i > 0:
                part_num = (i // self.groups_per_chunk) + 1
                chunk_parts.append(
                    f"\n**[Part {part_num}: Groups {i+1}-{chunk_end} "
                    f"of {len(groups)} total{table_context}]**\n"
                )
            else:
                chunk_parts.append(
                    f"\n**[Part 1: Groups 1-{chunk_end} "
                    f"of {len(groups)} total{table_context}]**\n"
                )
            
            chunk_parts.append('\n'.join(chunk_groups))
            
            result_chunk = '\n\n'.join(chunk_parts)
            chunks.append(result_chunk)
            
            if self.debug_mode:
                first_group = chunk_groups[0].split('\n')[0][:80] if chunk_groups else ""
                logger.debug(
                    f"  Chunk {len(chunks)}: {len(chunk_groups)} groups, "
                    f"{len(result_chunk)} chars | First: {first_group}..."
                )
        
        return chunks
