from pathlib import Path
from typing import Optional, List
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.openai import OpenAIEmbedder
from logger.logger import log_info, log_debug, log_error
from config.settings import Settings
import shutil

class KnowledgeBaseLoader:
    """Loader for PDF Knowledge Base with PostgreSQL vector storage."""

    def __init__(self, settings: Settings):
        """
        Initialize the knowledge base loader.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.kb_path = settings.KB_DIR
        self.pg_connection = settings.PG_CONNECTION_STRING
        self.openai_api_key = settings.OPENAI_API_KEY

        # Ensure the knowledge base directory exists
        if not Path(self.kb_path).exists():
            log_info(f"Knowledge base directory does not exist. Creating: {self.kb_path}")
            Path(self.kb_path).mkdir(parents=True, exist_ok=True)  # Automatically create directory if not exists

    def load_knowledge_base(self, table_name: str = "resume_kb", 
                            search_type: SearchType = SearchType.hybrid) -> Optional[PDFKnowledgeBase]:
        """
        Load the PDF knowledge base.

        Args:
            table_name: Name of the PostgreSQL table for vector storage
            search_type: Search type for vector database

        Returns:
            Loaded PDFKnowledgeBase instance or None if loading fails
        """
        try:
            log_info("Initializing PDF Knowledge Base")

            # Set up vector database
            vector_db = PgVector(
                table_name=table_name,
                db_url=self.pg_connection,
                search_type=search_type,
                embedder=OpenAIEmbedder(
                    api_key=self.openai_api_key,
                    id="text-embedding-3-small"
                ),
            )

            # Create and load knowledge base with 'path' parameter instead of 'location'
            kb = PDFKnowledgeBase(
                path=str(self.kb_path),  # Changed from 'location' to 'path'
                vector_db=vector_db,
            )

            # Load documents and create embeddings
            kb.load(upsert=True)

            log_info(f"Knowledge base loaded with documents from {self.kb_path}")
            return kb

        except Exception as e:
            log_error(f"Failed to load knowledge base: {str(e)}")
            return None

    def add_documents(self, docs_paths: List[str]) -> bool:
        """
        Add documents to the knowledge base.

        Args:
            docs_paths: List of paths to documents to add

        Returns:
            Success status
        """
        kb = self.load_knowledge_base()
        if not kb:
            return False

        try:
            for doc_path in docs_paths:
                path = Path(doc_path)
                if path.exists():
                    if path.suffix.lower() == '.pdf':
                        # Copy document to knowledge base directory
                        dest_path = Path(self.kb_path) / path.name
                        try:
                            shutil.copy2(path, dest_path)
                            log_debug(f"Added document to knowledge base: {path.name}")
                        except Exception as e:
                            log_error(f"Failed to copy document {path.name}: {str(e)}")
                    else:
                        log_error(f"Invalid file format, expected PDF: {doc_path}")
                else:
                    log_error(f"Document path does not exist: {doc_path}")

            # Reload knowledge base to update embeddings
            kb.load(upsert=True)
            log_info(f"Knowledge base updated with new documents")
            return True

        except Exception as e:
            log_error(f"Failed to add documents to knowledge base: {str(e)}")
            return False