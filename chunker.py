"""Text chunking utilities for processing large documents."""

import re
import logging
from typing import List, Optional
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class TextChunker:
    """Handles intelligent text chunking for large documents."""
    
    def __init__(
        self,
        max_tokens: int = 3500,
        tokenizer_name: str = "google/gemma-3-27b-it",
        debug_mode: bool = False
    ):
        """
        Initialize the text chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk.
            tokenizer_name: HuggingFace tokenizer model name (default: 'google/gemma-3-27b-it').
            debug_mode: Enable verbose logging.
        """
        self.max_tokens = max_tokens
        self.debug_mode = debug_mode
        self.tokenizer = self._load_tokenizer(tokenizer_name)
    
    def _load_tokenizer(self, tokenizer_name: str) -> Optional[AutoTokenizer]:
        """Load HuggingFace tokenizer for token counting."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
            logger.info("Tokenizer loaded successfully")
            return tokenizer
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}. Token counting disabled.")
            return None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the loaded tokenizer.
        
        Args:
            text: Text to count tokens in.
            
        Returns:
            Token count, or 0 if tokenizer unavailable.
        """
        if not self.tokenizer or not text:
            return 0
        
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return 0
    
    def chunk_by_headings_blackdesert(self, text: str) -> List[str]:
        """
        Split text by H2/H3 headings (playblackdesert.com structure).
        
        Looks for:
        - Lines starting with '### ' (H3 headings)
        - Lines followed by '---' (H2 underlined headings)
        
        Args:
            text: Markdown text to split.
            
        Returns:
            List of text chunks split by headings.
        """
        # Pattern: H3 headings OR text followed by dashes
        pattern = re.compile(r'(^### |^[A-Za-z][^\n]*\n-+$)', re.MULTILINE)
        matches = list(pattern.finditer(text))
        
        if not matches:
            logger.info("No H2/H3 headings found. Processing as single chunk.")
            return [text.strip()] if text.strip() else []
        
        # Create split points
        split_points = [0] + [m.start() for m in matches] + [len(text)]
        split_points = sorted(set(split_points))
        
        chunks = []
        for i in range(len(split_points) - 1):
            start = split_points[i]
            end = split_points[i + 1]
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
        
        logger.info(f"Split into {len(chunks)} chunks by H2/H3 headings")
        return chunks
    
    def chunk_by_headings_foundry(self, text: str) -> List[str]:
        """
        Split text by H2/H3/H4 headings (blackdesertfoundry.com structure).
        
        Looks for:
        - ATX-style: ##, ###, or #### headings
        - Setext-style: text followed by '---'
        
        Args:
            text: Markdown text to split.
            
        Returns:
            List of text chunks split by headings.
        """
        # ATX-style H2/H3/H4
        atx_pattern = r'^(?P<atx>#{2,4})\s+[^\n]+?\s*$'
        
        # Setext-style H2 (text line followed by dashes)
        setext_pattern = r'^(?P<setext>[^\s#][^\n]*?)\n-{3,}\s*$'
        
        combined = re.compile(
            rf'(?:{atx_pattern})|(?:{setext_pattern})',
            flags=re.MULTILINE
        )
        
        matches = list(combined.finditer(text))
        
        if not matches:
            return [text.strip()] if text.strip() else []
        
        split_points = [0] + [m.start() for m in matches] + [len(text)]
        split_points = sorted(set(split_points))
        
        chunks = []
        for i in range(len(split_points) - 1):
            start = split_points[i]
            end = split_points[i + 1]
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
        
        # Merge short preamble with first heading chunk
        if chunks and not self._starts_with_heading(chunks[0]):
            if len(chunks) > 1 and len(chunks[0]) < 120:
                chunks[1] = (chunks[0].rstrip() + "\n\n" + chunks[1].lstrip()).strip()
                chunks.pop(0)
        
        logger.info(f"Split into {len(chunks)} chunks by H2/H3/H4 headings")
        return chunks
    
    def chunk_by_headings_markdown(
        self,
        text: str,
        min_level: int = 2,
        include_setext: bool = True,
        include_numbered: bool = True,
        numbered_requires_hr: bool = True,
        merge_short_preamble: bool = True,
        preamble_threshold_chars: int = 160
    ) -> List[str]:
        """
        Generic markdown splitter:
        - ATX headings H{min_level..6} (e.g. ## ... ######)
        - Optional Setext-style headings (=== / ---)
        - Numbered section headings like '1. Title' (optionally require a '***' divider)
        - Merge short preamble with the first heading

        For the Garmoth site example: include_numbered=True and numbered_requires_hr=True are ideal.
        """
        if not text or not text.strip():
            return []

        # ---------- ATX ----------
        # Example: if min_level=2 this matches ##..######
        atx = rf'^(?P<atx>#{{{min_level},6}})\s+[^\n]+?\s*$'
        atx_re = re.compile(atx, re.MULTILINE)

        # ---------- Setext ----------
        setext_parts = []
        if include_setext:
            if 1 >= min_level:
                setext_parts.append(r'(?P<setext_h1>^[^\s#][^\n]*?)\n=+\s*$')
            if 2 >= min_level:
                setext_parts.append(r'(?P<setext_h2>^[^\s#][^\n]*?)\n-+\s*$')
        setext_re = re.compile('(?:' + '|'.join(setext_parts) + ')', re.MULTILINE) if setext_parts else None

        # ---------- Numbered ----------
        # Line example: "2.  What Is Throne Of Edana"
        numbered_line_re = re.compile(r'^(?P<num>\d+)\.\s+(?P<title>.+?)\s*$', re.MULTILINE)
        hr_re = re.compile(r'^\s*\*{3,}\s*$', re.MULTILINE)  # '***' or longer

        # Collect all matches → split positions
        split_positions = set([0, len(text)])

        # ATX
        for m in atx_re.finditer(text):
            split_positions.add(m.start())

        # Setext
        if setext_re:
            for m in setext_re.finditer(text):
                split_positions.add(m.start())

        # Numbered
        if include_numbered:
            for m in numbered_line_re.finditer(text):
                ok = True
                if numbered_requires_hr:
                    # True if there is a '***' within 1-3 lines after this heading
                    # (Blank lines are skipped)
                    line_end = text.find('\n', m.end())
                    if line_end == -1:
                        line_end = len(text)
                    # Check the next 3 lines
                    tail = text[line_end+1: ]
                    lines = tail.splitlines()
                    found_hr = False
                    check_upto = min(3, len(lines))
                    for i in range(check_upto):
                        s = lines[i].strip()
                        if not s:  # skip blank lines
                            continue
                        if hr_re.match(lines[i]):
                            found_hr = True
                            break
                        # If the first non-empty line isn't an hr, continue; allow 2-3 lines tolerance
                    ok = found_hr

                if ok:
                    split_positions.add(m.start())

        # Split
        points = sorted(split_positions)
        chunks = []
        for i in range(len(points) - 1):
            seg = text[points[i]:points[i+1]].strip()
            if seg:
                chunks.append(seg)

        # Merge short preamble with the first heading
        if merge_short_preamble and chunks and not self._starts_with_heading_any_or_numbered(chunks[0]):
            if len(chunks) > 1 and len(chunks[0]) <= preamble_threshold_chars:
                chunks[1] = (chunks[0].rstrip() + "\n\n" + chunks[1].lstrip()).strip()
                chunks.pop(0)

        return chunks
    
    def _starts_with_heading_any_or_numbered(self, text: str) -> bool:
        """
        Accepts lines starting with ATX H1–H6, Setext H1/H2, or numbered headings like '^\d+\. '.
        """
        return bool(re.match(
            r'^(#{1,6})\s+|^[^\n]+\n[-=]{3,}\s*$|^\s*\d+\.\s+[^\n]+$',
            text,
            re.MULTILINE
        ))

    
    def recombine_by_token_limit(self, chunks: List[str]) -> List[str]:
        """
        Recombine chunks to maximize token usage without exceeding limits.
        
        Groups non-heading chunks with the previous heading to form sections.
        Splits oversized chunks intelligently to preserve context.
        
        Args:
            chunks: List of raw text chunks.
            
        Returns:
            List of recombined chunks optimized for token limits.
        """
        if not chunks:
            return []
        
        heading_pattern = re.compile(
            r"^(#{1,6}\s+.+$|[^\s#].+\n[-=]{3,}\s*$)",
            re.MULTILINE
        )
        
        recombined = []
        current_section = ""
        can_count = bool(self.tokenizer)

        for idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue

            is_heading_start = bool(heading_pattern.match(chunk))

            # If this chunk starts a new heading and we already have a section,
            # flush the current section and start a new one with this chunk.
            if is_heading_start and current_section:
                recombined.append(current_section.strip())
                current_section = chunk
            else:
                if current_section:
                    # If tokenizer is available, check tokens before merging.
                    if can_count:
                        combined = (current_section + "\n\n" + chunk).strip()
                        try:
                            if self.count_tokens(combined) <= self.max_tokens:
                                current_section = combined
                            else:
                                # Do NOT include a partial of `chunk` in the current
                                # section. Flush current and start a new section
                                # with the whole chunk instead.
                                recombined.append(current_section.strip())
                                current_section = chunk
                        except Exception:
                            # On any token-counting error, fall back to simple concat
                            current_section += "\n\n" + chunk
                    else:
                        # Tokenizer unavailable: preserve previous behavior
                        current_section += "\n\n" + chunk
                else:
                    current_section = chunk

            if self.debug_mode:
                logger.debug(
                    f"Chunk {idx+1}/{len(chunks)} assigned to "
                    f"{'new' if is_heading_start else 'current'} section"
                )
        
        if current_section:
            recombined.append(current_section.strip())
        
        # Merge heading-only chunks with their content
        final_chunks = self._merge_orphaned_headings(recombined)
        
        # Split oversized chunks
        final_chunks = self._split_oversized_chunks(final_chunks)
        
        logger.info(
            f"{len(chunks)} initial chunks → {len(recombined)} sections → "
            f"{len(final_chunks)} final chunks"
        )
        return final_chunks
    
    def _merge_orphaned_headings(self, chunks: List[str]) -> List[str]:
        """Merge very short heading-only chunks with their following content."""
        heading_pattern = re.compile(
            r"^(#{1,6}\s+.+$|[^\s#].+\n[-=]{3,}\s*$)",
            re.MULTILINE
        )
        
        result = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            
            # Check if this is a very short chunk (< 15 words) that starts with a heading
            if len(current.split()) < 15 and heading_pattern.match(current):
                # Try to merge with next chunk
                if i + 1 < len(chunks):
                    merged = current.rstrip() + "\n\n" + chunks[i + 1].lstrip()
                    result.append(merged.strip())
                    i += 2  # Skip both chunks
                    continue
            
            result.append(current)
            i += 1
        
        return result
    
    def _split_oversized_chunks(self, chunks: List[str]) -> List[str]:
        """
        Split chunks exceeding token limit while preserving context.
        
        Each split part includes the section heading and continuation markers.
        
        Args:
            chunks: List of chunks to check and split.
            
        Returns:
            List with oversized chunks intelligently split.
        """
        if not self.tokenizer:
            logger.warning("Tokenizer unavailable, skipping oversized chunk splitting")
            return chunks
        
        result = []
        heading_pattern = re.compile(
            r"^(#{1,6}\s+.+$|[^\s#].+\n[-=]{3,}\s*$)",
            re.MULTILINE
        )
        
        for chunk_idx, chunk in enumerate(chunks):
            token_count = self.count_tokens(chunk)
            
            if token_count <= self.max_tokens:
                result.append(chunk)
                continue
            
            logger.warning(
                f"Oversized chunk detected: {token_count} tokens "
                f"(limit: {self.max_tokens}). Splitting chunk {chunk_idx + 1}..."
            )
            
            # Extract main heading
            lines = chunk.split('\n')
            heading_line, main_heading, content_start = self._extract_heading(lines)
            
            # Split content into blocks
            content_lines = lines[content_start:]
            blocks = self._split_into_blocks(content_lines, heading_pattern)
            
            # Combine blocks into sub-chunks within token limit
            sub_chunks = self._create_sub_chunks(
                blocks,
                heading_line,
                main_heading
            )
            
            result.extend(sub_chunks)
            logger.info(f"Split into {len(sub_chunks)} manageable sub-chunks")
        
        return result
    
    def _extract_heading(self, lines: List[str]) -> tuple:
        """Extract heading from lines. Returns (heading_line, heading_text, content_start_idx)."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # ATX-style heading (# ## ###)
            if stripped.startswith('#'):
                return line, stripped, i + 1
            
            # Setext-style heading (underlined with = or -)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'^[-=]{3,}\s*$', next_line):
                    heading_line = line + '\n' + lines[i + 1]
                    return heading_line, stripped, i + 2
        
        # No heading found
        return "## Content Section", "## Content Section", 0
    
    def _split_into_blocks(
        self,
        lines: List[str],
        heading_pattern: re.Pattern
    ) -> List[str]:
        """Split content lines into logical blocks (paragraphs, lists, etc.)."""
        blocks = []
        current_block = []
        
        for line in lines:
            stripped = line.strip()
            
            # Start new block on: heading, empty line after content, or bullet point
            should_split = (
                heading_pattern.match(stripped) or
                (not stripped and current_block and current_block[-1].strip()) or
                (stripped.startswith('*') and not line.startswith(' '))
            )
            
            if should_split and current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            
            current_block.append(line)
        
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    def _create_sub_chunks(
        self,
        blocks: List[str],
        heading_line: str,
        main_heading: str
    ) -> List[str]:
        """Combine blocks into sub-chunks that fit within token limit."""
        sub_chunks = []
        current_sub = []
        current_sub_tokens = 0
        
        heading_tokens = self.count_tokens(main_heading)
        reserve_tokens = heading_tokens + 100  # Extra for continuation text
        effective_limit = self.max_tokens - reserve_tokens
        
        for block in blocks:
            block_tokens = self.count_tokens(block)
            
            # If single block exceeds limit, split by sentences
            if block_tokens > effective_limit:
                if current_sub:
                    sub_chunks.append('\n\n'.join(current_sub))
                    current_sub = []
                    current_sub_tokens = 0
                
                # Split block by sentences
                sentences = re.split(r'(?<=[.!?])\s+', block)
                sentence_group = []
                sentence_tokens = 0
                
                for sent in sentences:
                    sent_tokens = self.count_tokens(sent)
                    
                    if sentence_tokens + sent_tokens > effective_limit and sentence_group:
                        sub_chunks.append('\n'.join(sentence_group))
                        sentence_group = [sent]
                        sentence_tokens = sent_tokens
                    else:
                        sentence_group.append(sent)
                        sentence_tokens += sent_tokens
                
                if sentence_group:
                    current_sub.append('\n'.join(sentence_group))
                    current_sub_tokens = sentence_tokens
            
            elif current_sub_tokens + block_tokens > effective_limit:
                # Current block would exceed limit
                if current_sub:
                    sub_chunks.append('\n\n'.join(current_sub))
                current_sub = [block]
                current_sub_tokens = block_tokens
            else:
                # Add block to current sub-chunk
                current_sub.append(block)
                current_sub_tokens += block_tokens
        
        # Add remaining content
        if current_sub:
            sub_chunks.append('\n\n'.join(current_sub))
        
        # Add headings and continuation markers
        return self._format_sub_chunks(sub_chunks, heading_line)
    
    def _format_sub_chunks(
        self,
        sub_chunks: List[str],
        heading_line: str
    ) -> List[str]:
        """Add headings and continuation markers to sub-chunks."""
        formatted = []
        
        for idx, sub_content in enumerate(sub_chunks):
            part_num = idx + 1
            total_parts = len(sub_chunks)
            
            if part_num == 1:
                # First part: original heading
                chunk = f"{heading_line}\n\n{sub_content}"
                if total_parts > 1:
                    chunk += f"\n\n**[Continued in Part {part_num + 1}]**"
            else:
                # Continuation parts
                chunk = (
                    f"{heading_line}\n\n"
                    f"**[Part {part_num} of {total_parts} - Continued]**\n\n"
                    f"{sub_content}"
                )
            
            formatted.append(chunk)
            
            if self.debug_mode:
                tokens = self.count_tokens(chunk)
                logger.debug(f"Sub-chunk {part_num}/{total_parts}: {tokens} tokens")
        
        return formatted
    
    def extract_heading_hierarchy(self, chunk: str) -> str:
        """
        Extract heading hierarchy from a chunk for context.
        
        Args:
            chunk: Markdown text chunk.
            
        Returns:
            String with hierarchical heading structure.
        """
        lines = chunk.split('\n')
        headings = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # ATX-style headings
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                headings.append((level, title))
                if len(headings) >= 3:
                    break
            
            # Setext-style H1 (=== underline)
            elif i + 1 < len(lines) and lines[i + 1].strip().startswith('==='):
                headings.append((1, line))
                if len(headings) >= 3:
                    break
            
            # Setext-style H2 (--- underline)
            elif i + 1 < len(lines) and re.match(r'^-{3,}\s*$', lines[i + 1].strip()):
                headings.append((2, line))
                if len(headings) >= 3:
                    break
        
        if not headings:
            return "Guide Section"
        
        # Build hierarchy string
        context_parts = []
        for level, title in headings:
            indent = "  " * (level - 1)
            context_parts.append(f"{indent}{'#' * level} {title}")
        
        return "\n".join(context_parts)
