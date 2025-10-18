"""LLM generation and JSONL output handling."""

import json
import re
import logging
import os
from typing import Dict, List, Optional

import google.generativeai as genai

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None

logger = logging.getLogger(__name__)


class DataGenerator:
    """Handles LLM-based data generation from text chunks."""
    
    def __init__(
        self,
        model_name: str,
        generation_config: Dict,
        safety_settings: List[Dict],
        meta_prompt_template: str,
        debug_mode: bool = False,
        tokenizer_name: str = "google/gemma-3-27b-it"
    ):
        """
        Initialize the data generator.
        
        Args:
            model_name: Google Generative AI model name.
            generation_config: Model generation configuration.
            safety_settings: Safety settings for generation.
            meta_prompt_template: Prompt template with {context} placeholder.
            debug_mode: Enable verbose logging.
            tokenizer_name: HuggingFace tokenizer model name (default: 'google/gemma-3-27b-it').
        """
        self.model_name = model_name
        self.generation_config = generation_config
        self.safety_settings = safety_settings
        self.meta_prompt_template = meta_prompt_template
        self.debug_mode = debug_mode
        self.tokenizer_name = tokenizer_name
        self.model = None
        self.tokenizer = None
        self._initialize_model()
        self._initialize_tokenizer()
    
    def _initialize_model(self):
        """Initialize the generative model with configuration."""
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            logger.info(f"Using API Key: {api_key[:4]}...")
            genai.configure(api_key=api_key)
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            logger.info(f"Model '{self.model_name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def _initialize_tokenizer(self):
        """Initialize tokenizer for accurate token counting."""
        if AutoTokenizer is None:
            logger.warning("transformers not installed, using word-based token estimation")
            return
        
        try:
            # Use the tokenizer name from configuration
            self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
            logger.info(f"Tokenizer '{self.tokenizer_name}' initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}. Using word-based estimation.")
            self.tokenizer = None
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tokenizer or word-based estimation."""
        if not text:
            return 0
        
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.debug(f"Tokenizer count failed: {e}")
        
        # Fallback: word-based estimation
        return int(len(text.split()) * 1.3)
    
    def generate_from_chunk(
        self,
        source_text: str,
        output_jsonl_path: str,
        url: str = "",
        date: str = "",
        guide_title: str = "",
        heading_context: str = ""
    ) -> int:
        """
        Generate JSONL data from a text chunk using LLM.
        
        Args:
            source_text: The content to generate data from.
            output_jsonl_path: Path to append JSONL output.
            url: Source URL for metadata.
            date: Publication/update date for metadata.
            guide_title: Guide title for context.
            heading_context: Hierarchical heading context.
            
        Returns:
            Number of lines written to file (0 on failure).
        """
        if not source_text:
            logger.error("Source text is empty")
            return 0
        
        try:
            # Build context string
            context_parts = []
            if guide_title:
                context_parts.append(f"Guide Title: {guide_title}")
            if heading_context:
                context_parts.append(f"Section Hierarchy:\n{heading_context}")
            context_str = "\n\n".join(context_parts)
            
            # Create final prompt
            final_prompt = self.meta_prompt_template.replace(
                "{context}",
                context_str
            ) + "\n" + source_text
            
            logger.info("Sending request to generator model...")
            response = self.model.generate_content(final_prompt)
            
            # Extract and clean response text
            cleaned_text = self._extract_response_text(response)
            
            if self.debug_mode:
                logger.debug(f"Raw model text:\n{cleaned_text[:500]}...")
            
            # Parse and validate JSON
            valid_lines = self._parse_and_validate_json(cleaned_text)
            
            if not valid_lines:
                logger.error("No valid JSONL output received from model")
                self._log_invalid_response(
                    output_jsonl_path,
                    cleaned_text,
                    url,
                    guide_title,
                    final_prompt  # Include the prompt in error log
                )
                return 0
            
            # Write to file
            lines_written = self._write_to_jsonl(
                output_jsonl_path,
                valid_lines,
                url,
                date
            )
            
            logger.info(
                f"Successfully appended {lines_written} entries to "
                f"'{output_jsonl_path}'"
            )
            return lines_written
        
        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            return 0
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Generative AI response object."""
        cleaned_text = ""
        
        if getattr(response, "text", None):
            cleaned_text = response.text or ""
        else:
            try:
                candidates = getattr(response, "candidates", []) or []
                parts = []
                for candidate in candidates:
                    content = getattr(candidate, "content", None)
                    if content:
                        candidate_parts = getattr(content, "parts", []) or []
                        for part in candidate_parts:
                            part_text = getattr(part, "text", None)
                            if part_text:
                                parts.append(part_text)
                cleaned_text = "".join(parts)
            except Exception as e:
                logger.warning(f"Error extracting text from response: {e}")
        
        cleaned_text = cleaned_text.strip()
        
        # Remove markdown code block markers
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()
        
        # Sanitize invalid JSON escapes
        cleaned_text = self._sanitize_json_escapes(cleaned_text)
        
        return cleaned_text
    
    def _sanitize_json_escapes(self, text: str) -> str:
        r"""
        Remove invalid JSON escape sequences.
        
        Fixes backslashes in invalid escapes like \* or \[.
        """
        if not text:
            return text
        
        # Replace invalid single-character escapes
        invalid_escape_re = re.compile(r'\\(?!["\\/bfnrtu])')
        sanitized = invalid_escape_re.sub(lambda m: m.group(0)[1:], text)
        
        # Handle incomplete unicode escapes
        sanitized = re.sub(r'\\u(?![0-9a-fA-F]{4})', 'u', sanitized)
        
        return sanitized
    
    def _parse_and_validate_json(self, text: str) -> List[str]:
        """
        Parse JSON/JSONL and validate structure.
        
        Supports both JSON array and JSONL formats.
        """
        valid_lines = []
        
        # Try parsing as JSON array first
        try:
            data_array = json.loads(text)
            if isinstance(data_array, list):
                logger.info("Model returned JSON array, processing as list")
                for item in data_array:
                    if self._is_valid_dialogue(item):
                        valid_lines.append(json.dumps(item, ensure_ascii=False))
                return valid_lines
        except json.JSONDecodeError:
            pass
        
        # Try parsing as JSONL (line by line)
        logger.info("Model returned JSONL format, processing line by line")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    item = json.loads(line)
                    if self._is_valid_dialogue(item):
                        valid_lines.append(json.dumps(item, ensure_ascii=False))
                except json.JSONDecodeError:
                    continue
        
        return valid_lines
    
    def _is_valid_dialogue(self, item: Dict) -> bool:
        """Validate dialogue structure."""
        if not isinstance(item, dict):
            return False
        
        conversations = item.get("conversations")
        if not isinstance(conversations, list) or len(conversations) < 2:
            return False
        
        # Check that each conversation has role and content
        for conv in conversations:
            if not isinstance(conv, dict):
                return False
            if "role" not in conv or "content" not in conv:
                return False
        
        return True
    
    def _write_to_jsonl(
        self,
        output_path: str,
        valid_lines: List[str],
        url: str = "",
        date: str = ""
    ) -> int:
        """Write validated JSON lines to JSONL file with metadata."""
        lines_written = 0
        
        try:
            with open(output_path, 'a', encoding='utf-8') as f:
                for line in valid_lines:
                    # Parse the JSON line
                    try:
                        item = json.loads(line)
                        
                        # Add metadata fields
                        item['url'] = url
                        item['lang'] = 'en'  # English content
                        if date:
                            item['date'] = date
                        
                        # Calculate answer tokens using tokenizer or word-based estimation
                        answer_tokens = 0
                        conversations = item.get('conversations', [])
                        for conv in conversations:
                            if conv.get('role') == 'assistant':
                                content = conv.get('content', '')
                                answer_tokens += self._count_tokens(content)
                        
                        item['answer_tokens'] = answer_tokens
                        
                        # Write enriched item
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                        lines_written += 1
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON line: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to write to file: {e}")
            return 0
        
        return lines_written
    
    def _log_invalid_response(
        self,
        output_jsonl_path: str,
        response_text: str,
        url: str,
        guide_title: str,
        final_prompt: str = ""
    ):
        """Log invalid model responses for debugging."""
        log_filename = output_jsonl_path.replace('.jsonl', '_errors.log')
        
        try:
            with open(log_filename, 'a', encoding='utf-8') as log_file:
                log_file.write("=" * 80 + "\n")
                log_file.write(f"URL: {url}\n")
                log_file.write(f"Guide Title: {guide_title}\n")
                log_file.write("-" * 80 + "\n")
                
                # Log the prompt that was sent to the model
                if final_prompt:
                    log_file.write("FINAL PROMPT SENT TO MODEL:\n")
                    log_file.write("-" * 80 + "\n")
                    log_file.write(final_prompt)
                    log_file.write("\n" + "-" * 80 + "\n\n")
                
                log_file.write("INVALID MODEL RESPONSE:\n")
                log_file.write(response_text[:2000])  # Truncate to 2000 chars
                if len(response_text) > 2000:
                    log_file.write(f"\n... [Truncated. Total length: {len(response_text)} chars]\n")
                log_file.write("\n" + "=" * 80 + "\n\n")
            
            logger.info(f"Invalid response logged to '{log_filename}'")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")


class ProcessedLinksTracker:
    """Track which URLs have been processed."""
    
    def __init__(self, links_file: str):
        """
        Initialize tracker.
        
        Args:
            links_file: Path to file storing processed URLs.
        """
        self.links_file = links_file
    
    def get_processed_links(self) -> set:
        """Load set of processed URLs from file."""
        if not os.path.exists(self.links_file):
            return set()
        
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to read processed links: {e}")
            return set()
    
    def mark_as_processed(self, url: str):
        """Add URL to processed links file."""
        try:
            with open(self.links_file, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
        except Exception as e:
            logger.error(f"Failed to mark link as processed: {e}")
