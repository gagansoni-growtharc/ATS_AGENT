"""
Custom Dual Logger for ATS: Logs to both MongoDB and Rich Console

This module provides a custom logger that extends the built-in logging.Logger
to log messages to both MongoDB and a styled console output using Rich.
"""

import logging
import datetime
from typing import Any, Dict, Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.text import Text
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

# Create Rich console for styled output
console = Console()

class AgnoLogger(logging.Logger):
    """Custom logger that logs to both MongoDB and console with Rich styling."""
    
    def __init__(self, name: str, db_uri: Optional[str] = None, 
                 collection_name: str = "logs", level=logging.INFO):
        super().__init__(name, level)
        
        # Set up Rich handler
        rich_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            console=console,
            show_time=True,
            show_level=True,
            show_path=False,
        )
        self.addHandler(rich_handler)
        
        # Set up MongoDB connection if URI provided
        self.mongo_collection = None
        if db_uri:
            try:
                client = MongoClient(db_uri)
                db = client.ats_agent
                self.mongo_collection = db[collection_name]
            except PyMongoError as e:
                console.print(f"[bold red]Failed to connect to MongoDB: {str(e)}[/bold red]")
    
    def _log_to_mongo(self, level: str, msg: str, source: str = "system", 
                      **extra: Dict[str, Any]) -> None:
        """Log a message to MongoDB collection."""
        if self.mongo_collection is None:
            return
            
        try:
            log_entry = {
                "timestamp": datetime.datetime.now(),
                "level": level,
                "message": msg,
                "source": source,
                **extra
            }
            self.mongo_collection.insert_one(log_entry)
        except PyMongoError as e:
            console.print(f"[bold red]Failed to log to MongoDB: {str(e)}[/bold red]")
    
    def info(self, msg: str, source: str = "system", center: bool = False, **kwargs):
        """Log an info message to both console and MongoDB."""
        if center:
            console.print(f"[bold blue]{'=' * 20} {msg} {'=' * 20}[/bold blue]")
        else:
            super().info(msg, **kwargs)
        self._log_to_mongo("INFO", msg, source, **kwargs)
    
    def debug(self, msg: str, source: str = "system", center: bool = False, **kwargs):
        """Log a debug message to both console and MongoDB."""
        if center:
            console.print(f"[cyan]{'- ' * 10} {msg} {' -' * 10}[/cyan]")
        else:
            super().debug(msg, **kwargs)
        self._log_to_mongo("DEBUG", msg, source, **kwargs)
    
    def warn(self, msg: str, source: str = "system", center: bool = False, **kwargs):
        """Log a warning message to both console and MongoDB."""
        if center:
            console.print(f"[yellow]{'! ' * 10} {msg} {' !' * 10}[/yellow]")
        else:
            super().warning(msg, **kwargs)
        self._log_to_mongo("WARNING", msg, source, **kwargs)
    
    def error(self, msg: str, source: str = "system", center: bool = False, **kwargs):
        """Log an error message to both console and MongoDB."""
        if center:
            console.print(f"[bold red]{'X ' * 10} {msg} {' X' * 10}[/bold red]")
        else:
            super().error(msg, **kwargs)
        self._log_to_mongo("ERROR", msg, source, **kwargs)
    
    def exception(self, msg: str, source: str = "system", **kwargs):
        """Log an exception message to both console and MongoDB."""
        super().exception(msg, **kwargs)
        self._log_to_mongo("EXCEPTION", msg, source, exc_info=True, **kwargs)


# Create a global instance of our logger
from config.settings import get_settings
settings = get_settings()
logger = AgnoLogger("ats_system", db_uri=settings.MONGO_URI, collection_name="ats_logs")

# Convenience functions for common log levels
def log_info(msg: str, source: str = "system", center: bool = False, **kwargs):
    logger.info(msg, source=source, center=center, **kwargs)

def log_debug(msg: str, source: str = "system", center: bool = False, **kwargs):
    logger.debug(msg, source=source, center=center, **kwargs)

def log_warn(msg: str, source: str = "system", center: bool = False, **kwargs):
    logger.warn(msg, source=source, center=center, **kwargs)

def log_error(msg: str, source: str = "system", center: bool = False, **kwargs):
    logger.error(msg, source=source, center=center, **kwargs)

def log_exception(msg: str, source: str = "system", **kwargs):
    logger.exception(msg, source=source, **kwargs)