"""
Refactored BDO Data Extraction Pipeline

A modular, maintainable data extraction pipeline for Black Desert Online guides.
Scrapes web content, cleans it, chunks it intelligently, and generates training
data using LLM.
"""

import logging
import time
import os
from typing import List

from dotenv import load_dotenv

from config import AppConfig
from scraper import WebScraper, extract_date_from_content, extract_links_from_markdown
from cleaner import clean_text
from chunker import TextChunker
from table_list_splitter import TableListSplitter
from generator import DataGenerator, ProcessedLinksTracker


# Configure logging
def setup_logging(debug_mode: bool = False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


class DataExtractionPipeline:
    """Main pipeline for extracting and generating training data from BDO guides."""
    
    def __init__(self, config: AppConfig):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config: Application configuration object.
        """
        self.config = config
        
        # Initialize components
        self.scraper = WebScraper(timeout=config.scraper.timeout)
        self.chunker = TextChunker(
            max_tokens=config.chunking.max_tokens,
            tokenizer_name=config.model.tokenizer_name,
            debug_mode=config.debug_mode
        )
        self.splitter = TableListSplitter(
            items_per_chunk=config.chunking.list_items_per_chunk,
            rows_per_chunk=config.chunking.table_rows_per_chunk,
            groups_per_chunk=config.chunking.nested_groups_per_chunk,
            min_long_list=config.chunking.min_long_list_items,
            min_long_table=config.chunking.min_long_table_rows,
            min_nested_groups=config.chunking.min_nested_groups,
            min_nested_items=config.chunking.min_nested_items,
            debug_mode=config.debug_mode
        )
        
        # Build generation config dict
        gen_config = {
            "temperature": config.generation.temperature,
            "top_p": config.generation.top_p,
            "top_k": config.generation.top_k,
            "max_output_tokens": config.generation.max_output_tokens,
        }
        
        self.generator = DataGenerator(
            model_name=config.generation.model_name,
            generation_config=gen_config,
            safety_settings=config.model.safety_settings,
            meta_prompt_template=config.model.meta_prompt_template,
            debug_mode=config.debug_mode,
            tokenizer_name=config.model.tokenizer_name
        )
        
        self.tracker = ProcessedLinksTracker(config.paths.processed_links_file)
    
    def process_url(self, url: str) -> int:
        """
        Process a single URL: scrape, clean, chunk, and generate data.
        
        Args:
            url: URL to process.
            
        Returns:
            Number of records generated.
        """
        logger.info(f"Processing URL: {url}")
        
        # Step 1: Scrape content
        content_data = self.scraper.scrape_content(url)
        if not content_data or not content_data.get("content"):
            logger.error("Failed to scrape content or content is empty")
            return 0
        
        original_content = content_data.get("content", "")
        guide_title = content_data.get("title", "").strip()
        actual_url = content_data.get("url", url)
        
        # Step 2: Extract date and clean content
        extracted_date = extract_date_from_content(original_content, url)
        cleaned_content = clean_text(original_content, url)
        
        if not cleaned_content:
            logger.error("Cleaned content is empty")
            return 0
        
        # Step 3: Chunk content based on domain
        final_chunks = self._chunk_content(url, cleaned_content)
        
        # Step 4: Generate data from each chunk
        total_records = 0
        for i, chunk in enumerate(final_chunks):
            logger.info(f"Processing chunk {i+1}/{len(final_chunks)}")
            
            # Check for long tables/lists and split further if needed
            sub_chunks = self._handle_long_structures(chunk, guide_title)
            
            for j, sub_chunk in enumerate(sub_chunks):
                if len(sub_chunks) > 1:
                    logger.info(f"  Sub-chunk {j+1}/{len(sub_chunks)}")
                
                # Extract heading context
                heading_context = self.chunker.extract_heading_hierarchy(sub_chunk)
                
                # Generate data
                for attempt in range(self.config.generation.retry_limit):
                    records = self.generator.generate_from_chunk(
                        source_text=sub_chunk,
                        output_jsonl_path=self.config.paths.output_filename,
                        url=actual_url,
                        date=extracted_date,
                        guide_title=guide_title,
                        heading_context=heading_context
                    )
                    
                    if records > 0:
                        total_records += records
                        break
                    
                    if attempt < self.config.generation.retry_limit - 1:
                        logger.warning(
                            f"Generation failed, retrying "
                            f"({attempt + 1}/{self.config.generation.retry_limit})..."
                        )
        
        logger.info(f"Completed URL processing. Generated {total_records} records.")
        return total_records
    
    def _chunk_content(self, url: str, content: str) -> List[str]:
        """
        Chunk content based on URL domain.
        
        Different domains have different heading structures.
        """
        if "playblackdesert.com" in url:
            logger.info("Using playblackdesert.com chunking strategy")
            initial_chunks = self.chunker.chunk_by_headings_blackdesert(content)
            return self.chunker.recombine_by_token_limit(initial_chunks)
        
        elif "blackdesertfoundry.com" in url:
            logger.info("Using blackdesertfoundry.com chunking strategy")
            initial_chunks = self.chunker.chunk_by_headings_foundry(content)
            return self.chunker.recombine_by_token_limit(initial_chunks)
        
        elif "garmoth.com" in url:
            logger.info("Using garmoth.com chunking strategy")
            initial_chunks = self.chunker.chunk_by_headings_markdown(content)
            return self.chunker.recombine_by_token_limit(initial_chunks)
        
        else:
            logger.info("Using default chunking (single chunk)")
            return [content]
    
    def _handle_long_structures(self, chunk: str, guide_title: str) -> List[str]:
        """
        Check for and split long tables/lists in chunk.
        
        Returns list of sub-chunks (or single chunk if no splitting needed).
        """
        # Check for nested bullet tables first (most specific)
        if self.splitter.detect_nested_bullet_table(chunk):
            return self.splitter.split_nested_bullet_table(chunk, guide_title)
        
        # Check for long tables
        if self.splitter.detect_long_table(chunk):
            return self.splitter.split_long_table(chunk, guide_title)
        
        # Check for long lists
        if self.splitter.detect_long_list(chunk):
            return self.splitter.split_long_list(chunk, guide_title)
        
        # No splitting needed
        return [chunk]
    
    def run_batch_mode(self):
        """Process all URLs from markdown file in batch mode."""
        logger.info("Running in BATCH mode")
        
        # Load all links
        all_links = extract_links_from_markdown(self.config.paths.markdown_filename)
        processed_links = self.tracker.get_processed_links()
        
        links_to_process = [
            link for link in all_links if link not in processed_links
        ]
        
        logger.info(
            f"Found {len(all_links)} total links. "
            f"{len(links_to_process)} new links to process."
        )
        
        if not links_to_process:
            logger.info("No new links to process. Exiting.")
            return 0
        
        # Process each link
        total_records = 0
        scraper_sleep = 60 / self.config.scraper.rate_limit
        
        for idx, link in enumerate(links_to_process):
            logger.info(
                f"\n{'='*80}\n"
                f"PROCESSING URL {idx+1}/{len(links_to_process)}\n"
                f"{'='*80}"
            )
            
            try:
                records = self.process_url(link)
                total_records += records
                
                # Mark as processed
                self.tracker.mark_as_processed(link)
                
            except Exception as e:
                logger.error(f"Critical error processing {link}: {e}", exc_info=True)
            
            # Rate limiting
            if idx < len(links_to_process) - 1:
                logger.info(f"Rate limiting: waiting {scraper_sleep:.1f}s...")
                time.sleep(scraper_sleep)
        
        return total_records
    
    def run_single_mode(self):
        """Process a single URL specified in configuration."""
        logger.info("Running in SINGLE URL mode")
        
        try:
            records = self.process_url(self.config.target_url)
            return records
        except Exception as e:
            logger.error(
                f"Critical error processing {self.config.target_url}: {e}",
                exc_info=True
            )
            return 0


def main():
    """Main entry point for the data extraction pipeline."""
    # Load environment variables
    try:
        load_dotenv()
    except ImportError:
        logger.warning(
            "python-dotenv not installed. "
            "If using .env file, install it with: pip install python-dotenv"
        )
    
    # Load configuration (can be customized here)
    config = AppConfig()
    
    # Setup logging
    setup_logging(debug_mode=config.debug_mode)
    
    logger.info("="*80)
    logger.info("BDO DATA EXTRACTION PIPELINE")
    logger.info("="*80)
    logger.info(f"Model: {config.generation.model_name}")
    logger.info(f"Batch mode: {config.batch_mode}")
    logger.info(f"Debug mode: {config.debug_mode}")
    logger.info(f"Output file: {config.paths.output_filename}")
    logger.info("="*80)
    
    # Initialize and run pipeline
    pipeline = DataExtractionPipeline(config)
    
    if config.batch_mode:
        total_records = pipeline.run_batch_mode()
    else:
        total_records = pipeline.run_single_mode()
    
    logger.info("="*80)
    logger.info(f"PIPELINE COMPLETED")
    logger.info(f"Total new records created: {total_records}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
