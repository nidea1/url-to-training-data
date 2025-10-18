"""Configuration settings for the BDO data extraction pipeline.

This module supports configuration via environment variables for easy deployment
and customization. All settings can be overridden by setting appropriate environment
variables (see .env.example for all available options).

Examples:
    Basic usage with defaults:
        config = AppConfig()
    
    With environment variables:
        export GENERATION_MODEL_NAME=gemini-2.0-flash
        export APP_DEBUG_MODE=true
        config = AppConfig()
    
    Programmatic override:
        config = AppConfig()
        config.generation.temperature = 0.8
"""

import os
from dataclasses import dataclass


def _get_env_str(key: str, default: str) -> str:
    """Get string environment variable with fallback to default."""
    return os.getenv(key, default)


def _get_env_int(key: str, default: int) -> int:
    """Get integer environment variable with fallback to default."""
    try:
        value = os.getenv(key)
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _get_env_float(key: str, default: float) -> float:
    """Get float environment variable with fallback to default."""
    try:
        value = os.getenv(key)
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def _get_env_bool(key: str, default: bool) -> bool:
    """Get boolean environment variable with fallback to default.
    
    Recognizes: 'true', '1', 'yes', 'on' as True
    Recognizes: 'false', '0', 'no', 'off' as False
    """
    value = os.getenv(key)
    if value is None:
        return default
    
    value_lower = str(value).lower().strip()
    if value_lower in ("true", "1", "yes", "on"):
        return True
    elif value_lower in ("false", "0", "no", "off"):
        return False
    return default


@dataclass
class ScraperConfig:
    """Configuration for web scraping.
    
    Environment variables:
        SCRAPER_RATE_LIMIT: Maximum requests per minute (default: 20)
        SCRAPER_TIMEOUT: Request timeout in seconds (default: 180)
    """
    rate_limit: int = None  # Requests per minute
    timeout: int = None  # Seconds
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.rate_limit is None:
            self.rate_limit = _get_env_int("SCRAPER_RATE_LIMIT", 20)
        if self.timeout is None:
            self.timeout = _get_env_int("SCRAPER_TIMEOUT", 180)


@dataclass
class GenerationConfig:
    """Configuration for LLM text generation.
    
    Environment variables:
        GENERATION_MODEL_NAME: Model to use (default: 'gemma-3-27b-it')
            Options: 'gemini-2.0-flash', 'gemini-2.0-pro', 'gemini-1.5-pro',
                    'gemini-1.5-flash', 'gemma-3-27b-it'
        GENERATION_TEMPERATURE: Model temperature 0-2 (default: 0.6)
        GENERATION_TOP_P: Nucleus sampling parameter 0-1 (default: 0.85)
        GENERATION_TOP_K: Top-K sampling (default: 32)
        GENERATION_MAX_OUTPUT_TOKENS: Maximum output tokens (default: 10240)
        GENERATION_RETRY_LIMIT: Retry attempts on failure (default: 1)
    """
    model_name: str = None
    temperature: float = None
    top_p: float = None
    top_k: int = None
    max_output_tokens: int = None
    retry_limit: int = None
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.model_name is None:
            self.model_name = _get_env_str("GENERATION_MODEL_NAME", "gemma-3-27b-it")
        if self.temperature is None:
            self.temperature = _get_env_float("GENERATION_TEMPERATURE", 0.6)
        if self.top_p is None:
            self.top_p = _get_env_float("GENERATION_TOP_P", 0.85)
        if self.top_k is None:
            self.top_k = _get_env_int("GENERATION_TOP_K", 32)
        if self.max_output_tokens is None:
            self.max_output_tokens = _get_env_int("GENERATION_MAX_OUTPUT_TOKENS", 10240)
        if self.retry_limit is None:
            self.retry_limit = _get_env_int("GENERATION_RETRY_LIMIT", 1)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking.
    
    Environment variables:
        CHUNKING_MAX_TOKENS: Maximum tokens per chunk (default: 3500)
        CHUNKING_LIST_ITEMS_PER_CHUNK: List items per chunk (default: 12)
        CHUNKING_TABLE_ROWS_PER_CHUNK: Table rows per chunk (default: 8)
        CHUNKING_NESTED_GROUPS_PER_CHUNK: Nested groups per chunk (default: 8)
        CHUNKING_MIN_LONG_LIST_ITEMS: Threshold for list splitting (default: 25)
        CHUNKING_MIN_LONG_TABLE_ROWS: Threshold for table splitting (default: 15)
        CHUNKING_MIN_NESTED_GROUPS: Threshold for nested table detection (default: 5)
        CHUNKING_MIN_NESTED_ITEMS: Threshold for nested items detection (default: 12)
    """
    max_tokens: int = None
    list_items_per_chunk: int = None
    table_rows_per_chunk: int = None
    nested_groups_per_chunk: int = None
    min_long_list_items: int = None
    min_long_table_rows: int = None
    min_nested_groups: int = None
    min_nested_items: int = None
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.max_tokens is None:
            self.max_tokens = _get_env_int("CHUNKING_MAX_TOKENS", 3500)
        if self.list_items_per_chunk is None:
            self.list_items_per_chunk = _get_env_int("CHUNKING_LIST_ITEMS_PER_CHUNK", 12)
        if self.table_rows_per_chunk is None:
            self.table_rows_per_chunk = _get_env_int("CHUNKING_TABLE_ROWS_PER_CHUNK", 8)
        if self.nested_groups_per_chunk is None:
            self.nested_groups_per_chunk = _get_env_int("CHUNKING_NESTED_GROUPS_PER_CHUNK", 8)
        if self.min_long_list_items is None:
            self.min_long_list_items = _get_env_int("CHUNKING_MIN_LONG_LIST_ITEMS", 25)
        if self.min_long_table_rows is None:
            self.min_long_table_rows = _get_env_int("CHUNKING_MIN_LONG_TABLE_ROWS", 15)
        if self.min_nested_groups is None:
            self.min_nested_groups = _get_env_int("CHUNKING_MIN_NESTED_GROUPS", 5)
        if self.min_nested_items is None:
            self.min_nested_items = _get_env_int("CHUNKING_MIN_NESTED_ITEMS", 12)


@dataclass
class QualityRules:
    """Quality validation rules for generated data.
    
    Environment variables:
        QUALITY_MIN_PAIRS_PER_CHUNK: Minimum dialogue pairs (default: 10)
        QUALITY_MAX_PAIRS_PER_CHUNK: Maximum dialogue pairs (default: 30)
        QUALITY_MIN_INSTRUCTION_WORDS: Minimum words in question (default: 6)
        QUALITY_MAX_INSTRUCTION_WORDS: Maximum words in question (default: 48)
        QUALITY_MIN_OUTPUT_WORDS: Minimum words in answer (default: 14)
        QUALITY_MAX_OUTPUT_WORDS: Maximum words in answer (default: 200)
    """
    min_pairs_per_chunk: int = None
    max_pairs_per_chunk: int = None
    min_instruction_words: int = None
    max_instruction_words: int = None
    min_output_words: int = None
    max_output_words: int = None
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.min_pairs_per_chunk is None:
            self.min_pairs_per_chunk = _get_env_int("QUALITY_MIN_PAIRS_PER_CHUNK", 10)
        if self.max_pairs_per_chunk is None:
            self.max_pairs_per_chunk = _get_env_int("QUALITY_MAX_PAIRS_PER_CHUNK", 30)
        if self.min_instruction_words is None:
            self.min_instruction_words = _get_env_int("QUALITY_MIN_INSTRUCTION_WORDS", 6)
        if self.max_instruction_words is None:
            self.max_instruction_words = _get_env_int("QUALITY_MAX_INSTRUCTION_WORDS", 48)
        if self.min_output_words is None:
            self.min_output_words = _get_env_int("QUALITY_MIN_OUTPUT_WORDS", 14)
        if self.max_output_words is None:
            self.max_output_words = _get_env_int("QUALITY_MAX_OUTPUT_WORDS", 200)


@dataclass
class PathConfig:
    """File paths for input/output.
    
    Environment variables:
        PATHS_MARKDOWN_FILENAME: Input markdown file with links (default: './official/LINKS.md')
        PATHS_PROCESSED_LINKS_FILE: Processed links tracker (default: './official/processed_links.txt')
        PATHS_OUTPUT_FILENAME: Output JSONL file (default: 'bdo_official_guides.jsonl')
        PATHS_SHORT_CHUNKS_LOG: Short chunks log file (default: './short_chunks.log')
    """
    markdown_filename: str = None
    processed_links_file: str = None
    output_filename: str = None
    short_chunks_log: str = None
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.markdown_filename is None:
            self.markdown_filename = _get_env_str("PATHS_MARKDOWN_FILENAME", "./official/LINKS.md")
        if self.processed_links_file is None:
            self.processed_links_file = _get_env_str("PATHS_PROCESSED_LINKS_FILE", "./official/processed_links.txt")
        if self.output_filename is None:
            self.output_filename = _get_env_str("PATHS_OUTPUT_FILENAME", "./outputs/bdo_official_guides.jsonl")
        if self.short_chunks_log is None:
            self.short_chunks_log = _get_env_str("PATHS_SHORT_CHUNKS_LOG", "./outputs/short_chunks.log")


@dataclass
class ModelConfig:
    """Configuration for model-specific settings.
    
    Environment variables:
        MODEL_TOKENIZER_NAME: HuggingFace tokenizer model name (default: 'google/gemma-3-27b-it')
        MODEL_SAFETY_SETTINGS_TEMPLATE: JSON string for safety settings override (optional)
        MODEL_META_PROMPT_FILE: File path for meta prompt template (optional, uses default if not set)
    """
    tokenizer_name: str = None
    safety_settings: list = None
    meta_prompt_template: str = None
    
    def __post_init__(self):
        """Load from environment variables."""
        if self.tokenizer_name is None:
            self.tokenizer_name = _get_env_str("MODEL_TOKENIZER_NAME", "google/gemma-3-27b-it")
        
        # Safety settings default
        if self.safety_settings is None:
            self.safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUAL", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        
        # Meta prompt template - use environment variable to load from file if provided
        if self.meta_prompt_template is None:
            prompt_file = os.getenv("MODEL_META_PROMPT_FILE")
            if prompt_file and os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        self.meta_prompt_template = f.read()
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to load meta prompt from {prompt_file}: {e}. Using default.")
                    self.meta_prompt_template = self._get_default_meta_prompt()
            else:
                self.meta_prompt_template = self._get_default_meta_prompt()
    
    @staticmethod
    def _get_default_meta_prompt() -> str:
        """Return the default meta prompt template."""
        return """
You are an expert Black Desert Online player and guide creator. Your task is to generate a high-quality English conversational training dataset for an AI assistant specialized in helping BDO players.

**INSTRUCTIONS:**
1.  Carefully read the guide content under "[SOURCE TEXT]" and the context provided under "[CONTEXT]".
2.  **CRITICAL - Context Integration:** You MUST interpret the [CONTEXT] block to guide your question generation.
    - **Parse the Context:**
        - Identify the **Main Topic** from the "Guide Title" (e.g., if 'Guide Title: Season Pass Guide', the main topic is 'Season Pass').
        - Identify the **Specific Sub-Topic** from the "Section Hierarchy" (e.g., if 'Section Hierarchy: ### Tuvala Gear', the sub-topic is 'Tuvala Gear').
        - **SPECIAL: Table/List Context** - If you see a note like "[Part 1: Rows 1-8 of 11 total - <ITEM_NAME>]", you MUST use the specific item name in your questions.
        - **CONTINUATION CONTEXT** - If you see "[Part X of Y - Continued]", this means you're reading a continuation of a longer section. The heading shows the overall topic, and you should generate questions that naturally refer to this specific part while maintaining awareness of the broader context.
    - **Combine Topics in Questions:** You MUST weave both the **Main Topic** and the **Specific Sub-Topic** (and any Table/List specific identifiers) into your questions naturally. This is the most important rule.
    - **BAD EXAMPLES (Missing Context):**
        - "What materials are needed?" ❌ (Which materials? For what?)
        - "How do I enhance it?" ❌ (Enhance what?)
        - "What are the stats at PEN level?" ❌ (Which item? Missing specific identifier!)
    - **GOOD EXAMPLES (Natural & Combined Context):**
        - "Regarding the Season Pass, what materials do I need for Tuvala gear enhancement?" ✓ (Combines Main Topic + Sub-Topic)
        - "For my season character's Tuvala gear, how does the enhancement process work?" ✓
        - "What are the Season Pass requirements for enhancing Tuvala armor?" ✓
        - "What are the stats for <ITEM_NAME> at PEN (V) enhancement level?" ✓ (Includes specific item name from table context)
        - "How much DP does <ITEM_NAME> give at TET (IV)?" ✓ (Specific item name in question)
3.  **Principle of Comprehensive Coverage:** Your primary goal is to **extract every distinct piece of information** from the [SOURCE TEXT].
4.  **Dynamic Quantity Guideline:** For dense sections with lots of data (like enhancement tables or item lists), you **must generate significantly more** dialogues. Completeness is key.
5.  **CRITICAL - Enhancement Tables & Lists Processing:** 
    - **MANDATORY: One QA pair per table row/list item** - You MUST create AT LEAST one question-answer pair for EACH row in enhancement tables or EACH item in lists.
    - **Enhancement Level Tables** (e.g., gear stats at +0, PRI, DUO, TRI, TET, PEN, etc.):
      - Create questions for EVERY enhancement level shown in the table
      - Each row represents a different enhancement level and MUST have its own QA pair
      - Example: If table has 11 rows (+0 through DEC), generate AT LEAST 11 distinct QA pairs
    - **Requirement/Material Tables** (e.g., materials needed per level):
      - Each row's requirements must be covered separately
    - **Item Lists** (e.g., rewards, drops, materials):
      - Each distinct item in the list needs its own QA pair
    - **NO GENERIC ANSWERS**: Instead of "The table shows various stats", specify exact values for each level
    - **BAD EXAMPLE**: ❌ "The gear provides different stats at different enhancement levels" (too vague)
    - **GOOD EXAMPLES**: 
      - ✅ "What's the DP for <ITEM_NAME> at +0?" → "At +0 enhancement, <ITEM_NAME> provides <VALUE> DP."
      - ✅ "How much evasion does <ITEM_NAME> give at PRI (I)?" → "At PRI (I) enhancement, it provides <VALUE> evasion (<VALUE> when combined with other stats)."
      - ✅ "What are the Max HP stats for <ITEM_NAME> at DEC (X)?" → "At DEC (X) enhancement, <ITEM_NAME> provides <VALUE> Max HP."
6.  **Generate Deep Multi-Turn Dialogues:** Create realistic dialogues (2-5 exchanges). Simulate flows like clarification, correction, or simple follow-ups.
7.  **Generate Diverse Question Archetypes:** Create a mix of question types: How-to, Why, Comparison, Location, Requirement, and Hypothetical questions.

**OUTPUT FORMAT (STRICT JSON ARRAY):**
-   Return ONLY a valid JSON array of dialogue objects. NO Markdown, NO JSONL, NO extra text.
-   Each dialogue object must follow this exact schema:

EXAMPLE 1 - General Guide Question:
{
    "conversations": [
        {
            "role": "system",
            "content": "You are a domain-restricted assistant specialized in Black Desert Online (BDO). If the user's question is not related to Black Desert Online, politely state your specialization and decline to answer. If the provided guide text does not contain enough information to answer a BDO-related question, reply exactly with: \\"I don't know.\\""
        },
        {
            "role": "user",
            "content": "For my season character, what do I need to enhance Tuvala gear?"
        },
        {
            "role": "assistant",
            "content": "To enhance Tuvala gear during the season, you primarily need 'Time-filled Blackstones' for the enhancement attempts and 'Tuvala Ore' to repair the gear's maximum durability."
        },
        {
            "role": "user",
            "content": "Where can I get those Time-filled Blackstones?"
        },
        {
            "role": "assistant",
            "content": "You can obtain Time-filled Blackstones from various sources, including Season Pass rewards, weekly season quests, and by grinding in designated monster zones in Valencia, Kamasylvia, Drieghan, and O'dyllita."
        }
    ]
}

EXAMPLE 2 - Enhancement Table Question (MANDATORY FORMAT):
{
    "conversations": [
        {
            "role": "system",
            "content": "You are a domain-restricted assistant specialized in Black Desert Online (BDO). If the user's question is not related to Black Desert Online, politely state your specialization and decline to answer. If the provided guide text does not contain enough information to answer a BDO-related question, reply exactly with: \\"I don't know.\\""
        },
        {
            "role": "user",
            "content": "What are the stats for <ITEM_NAME> at PRI (I) enhancement level?"
        },
        {
            "role": "assistant",
            "content": "At PRI (I) enhancement level, <ITEM_NAME> provides <VALUE> DP, <VALUE> evasion (<VALUE> with additional stats), <VALUE> damage reduction (<VALUE> with additional stats), <VALUE> Monster DR, and <VALUE> Max HP."
        }
    ]
}

EXAMPLE 3 - Specific Stat Question for Single Enhancement Level:
{
    "conversations": [
        {
            "role": "system",
            "content": "You are a domain-restricted assistant specialized in Black Desert Online (BDO). If the user's question is not related to Black Desert Online, politely state your specialization and decline to answer. If the provided guide text does not contain enough information to answer a BDO-related question, reply exactly with: \\"I don't know.\\""
        },
        {
            "role": "user",
            "content": "How much Max HP does <ITEM_NAME> give at DEC (X)?"
        },
        {
            "role": "assistant",
            "content": "At DEC (X) enhancement level, <ITEM_NAME> provides <VALUE> Max HP."
        }
    ]
}

**CONTENT QUALITY RULES:**
-   **Questions:** Must be natural and varied. **CRITICAL: They must naturally integrate the Main Topic (from Guide Title), the Sub-Topic (from Section Hierarchy), AND any specific identifiers from Table/List context notes (extracted from the actual source text).**
-   **Answers:** Must be factually grounded in the [SOURCE TEXT] ONLY. If info is missing, respond with "I don't know."
-   **Negative & Boundary Questions:** Include 10-20% off-topic or boundary-testing questions (unrelated, out of scope, incorrect premise, etc.).
-   **Negative & Boundary Questions:** Include 10-20% off-topic or boundary-testing questions (unrelated, out of scope, incorrect premise, etc.).
    - **OFF-TOPIC EXAMPLES:** These should be realistic user prompts that are clearly unrelated to BDO or the guide content. Include both short casual queries and longer mistaken-premise questions. Labeling is not required in the output, but the generation process must include this mix.
        - Real-world unrelated topics (weather, sports, cooking, travel, history, etc.)
        - Other games (MMORPGs, FPS, strategy games, etc.)
        - Non-gaming technology topics (AI, blockchain, etc.)
        - Generic AI questions (e.g., "What is the meaning of life?", "How do I bake a cake?")
    - When the model encounters off-topic prompts during generation, the assistant in the conversation should follow the system message rule: politely state the specialization and decline to answer if not BDO-related, or reply exactly with "I don't know." when the guide lacks relevant info.

**VALIDATION CHECKLIST:**
✓ Output is a raw JSON array.
✓ Output quantity is driven by content density.
✓ Every concept, table, and list is represented.
✓ **MANDATORY: For enhancement tables, AT LEAST one QA pair exists for EACH enhancement level row (e.g. +0 to +15 or PRI to DEC or +0 to DEC).**
✓ **MANDATORY: For item/reward lists, AT LEAST one QA pair exists for EACH distinct item.**
✓ A variety of question archetypes are present.
✓ **CRITICAL: The first user question in EVERY conversation weaves context NATURALLY from the 'Guide Title', 'Section Hierarchy', AND any specific Table/List identifiers (extracted from the actual source text).**
✓ **TABLES: When asking about table data, user questions MUST include the specific item/entity name from the source text (replace <ITEM_NAME> placeholders with actual names).**
✓ **TABLES: Questions must specify the EXACT enhancement level (e.g., "at PRI (I)" or "at TET (IV)") - no generic "at higher levels" questions.**
✓ Questions sound NATURAL.
✓ All responses are grounded in the source text or are proper rejections.

[CONTEXT]
{context}

[SOURCE TEXT]
"""


@dataclass
class AppConfig:
    """Main application configuration.
    
    Environment variables:
        APP_TARGET_URL: Single URL to process (default: official BDO wiki)
        APP_DEBUG_MODE: Enable verbose logging (default: false)
        APP_BATCH_MODE: Process URLs from file vs single URL (default: true)
        GOOGLE_API_KEY: Google Generative AI API key (REQUIRED)
    
    All nested configurations (scraper, generation, etc.) also support
    environment variables as documented in their respective classes.
    """
    target_url: str = None
    debug_mode: bool = None
    batch_mode: bool = None
    
    scraper: ScraperConfig = None
    generation: GenerationConfig = None
    chunking: ChunkingConfig = None
    quality: QualityRules = None
    paths: PathConfig = None
    model: ModelConfig = None
    
    def __post_init__(self):
        """Initialize nested configurations and load from environment variables."""
        # Load main settings from environment
        if self.target_url is None:
            self.target_url = _get_env_str("APP_TARGET_URL", "")
        if self.debug_mode is None:
            self.debug_mode = _get_env_bool("APP_DEBUG_MODE", False)
        if self.batch_mode is None:
            self.batch_mode = _get_env_bool("APP_BATCH_MODE", True)
        
        if not self.batch_mode and not self.target_url:
            raise ValueError("APP_TARGET_URL must be set when APP_BATCH_MODE is false.")
        
        # Initialize nested configurations
        if self.scraper is None:
            self.scraper = ScraperConfig()
        if self.generation is None:
            self.generation = GenerationConfig()
        if self.chunking is None:
            self.chunking = ChunkingConfig()
        if self.quality is None:
            self.quality = QualityRules()
        if self.paths is None:
            self.paths = PathConfig()
        if self.model is None:
            self.model = ModelConfig()


META_QUESTION_KEYWORDS = (
    "text",
    "passage",
    "paragraph",
    "document",
    "section",
    "article",
    "prompt",
    "sentence",
    "source",
)
