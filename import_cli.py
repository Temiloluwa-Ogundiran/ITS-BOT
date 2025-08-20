#!/usr/bin/env python3
"""
Command-Line Interface for Knowledge Base Content Import

Provides a command-line interface for importing knowledge base content
from various file formats with validation and error reporting.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from csv_importer import CSVImporter, ImportResult
from json_importer import JSONImporter
from excel_importer import ExcelImporter
from content_validator import ContentValidator
from helpdesk_elasticsearch import HelpdeskElasticsearchManager


class ImportCLI:
    """Command-line interface for the import system."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.setup_logging()
        self.es_manager = None
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('import.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_elasticsearch(self, host: str = "localhost", port: int = 9200):
        """Connect to Elasticsearch."""
        try:
            self.es_manager = HelpdeskElasticsearchManager(host=host, port=port)
            if self.es_manager._test_connection():
                self.logger.info(f"Connected to Elasticsearch at {host}:{port}")
                return True
            else:
                self.logger.error("Failed to connect to Elasticsearch")
                return False
        except Exception as e:
            self.logger.error(f"Elasticsearch connection failed: {e}")
            return False
    
    def import_csv(self, file_path: str, preview_mode: bool = False) -> ImportResult:
        """Import from CSV file."""
        self.logger.info(f"Starting CSV import from: {file_path}")
        
        importer = CSVImporter(self.es_manager)
        result = importer.import_from_csv(file_path, preview_mode=preview_mode)
        
        self._print_import_result(result, "CSV")
        return result
    
    def import_json(self, file_path: str, preview_mode: bool = False, 
                   update_existing: bool = False) -> ImportResult:
        """Import from JSON file."""
        self.logger.info(f"Starting JSON import from: {file_path}")
        
        importer = JSONImporter(self.es_manager)
        result = importer.import_from_json(file_path, preview_mode, update_existing)
        
        self._print_import_result(result, "JSON")
        return result
    
    def import_excel(self, file_path: str, preview_mode: bool = False) -> ImportResult:
        """Import from Excel file."""
        self.logger.info(f"Starting Excel import from: {file_path}")
        
        try:
            importer = ExcelImporter(self.es_manager)
            result = importer.import_from_excel(file_path, preview_mode)
            
            self._print_import_result(result, "Excel")
            return result
        except ImportError as e:
            self.logger.error(f"Excel import failed: {e}")
            return ImportResult(
                success=False,
                total_records=0,
                successful_imports=0,
                failed_imports=1,
                errors=[{"type": "import_error", "message": str(e)}],
                warnings=[],
                processing_time=0.0
            )
    
    def validate_file(self, file_path: str, file_type: str):
        """Validate a file without importing."""
        self.logger.info(f"Validating {file_type} file: {file_path}")
        
        if file_type == "csv":
            importer = CSVImporter()
            result = importer.import_from_csv(file_path, preview_mode=True)
        elif file_type == "json":
            importer = JSONImporter()
            result = importer.import_from_json(file_path, preview_mode=True)
        elif file_type == "excel":
            try:
                importer = ExcelImporter()
                result = importer.import_from_excel(file_path, preview_mode=True)
            except ImportError as e:
                self.logger.error(f"Excel validation failed: {e}")
                return
        else:
            self.logger.error(f"Unsupported file type: {file_type}")
            return
        
        self._print_validation_result(result, file_type)
    
    def _print_import_result(self, result: ImportResult, file_type: str):
        """Print import result summary."""
        print(f"\n{'='*60}")
        print(f"{file_type.upper()} IMPORT RESULT")
        print(f"{'='*60}")
        
        if result.success:
            print("✅ Import completed successfully!")
        else:
            print("❌ Import completed with errors")
        
        print(f"\n📊 Summary:")
        print(f"   Total records processed: {result.total_records}")
        print(f"   Successful imports: {result.successful_imports}")
        print(f"   Failed imports: {result.failed_imports}")
        print(f"   Processing time: {result.processing_time:.2f} seconds")
        
        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                row_info = f" (Row {error['row_number']})" if error.get('row_number') else ""
                print(f"   {i}. {error['type']}{row_info}: {error['message']}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings, 1):
                print(f"   {i}. {warning}")
        
        print(f"\n{'='*60}")
    
    def _print_validation_result(self, result: ImportResult, file_type: str):
        """Print validation result summary."""
        print(f"\n{'='*60}")
        print(f"{file_type.upper()} VALIDATION RESULT")
        print(f"{'='*60}")
        
        if result.success:
            print("✅ File validation passed!")
        else:
            print("❌ File validation failed")
        
        print(f"\n📊 Summary:")
        print(f"   Total records: {result.total_records}")
        print(f"   Valid records: {result.successful_imports}")
        print(f"   Invalid records: {result.failed_imports}")
        
        if result.errors:
            print(f"\n❌ Validation Errors ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                row_info = f" (Row {error['row_number']})" if error.get('row_number') else ""
                print(f"   {i}. {error['type']}{row_info}: {error['message']}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for i, warning in enumerate(result.warnings, 1):
                print(f"   {i}. {warning}")
        
        print(f"\n{'='*60}")
    
    def run(self):
        """Run the CLI."""
        parser = argparse.ArgumentParser(
            description="Knowledge Base Content Import Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Import CSV file
  python import_cli.py import csv articles.csv
  
  # Preview CSV file without importing
  python import_cli.py import csv articles.csv --preview
  
  # Import JSON file with updates
  python import_cli.py import json articles.json --update-existing
  
  # Validate Excel file
  python import_cli.py validate excel articles.xlsx
  
  # Import with custom Elasticsearch connection
  python import_cli.py import csv articles.csv --es-host localhost --es-port 9200
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Import command
        import_parser = subparsers.add_parser('import', help='Import content from files')
        import_parser.add_argument('file_type', choices=['csv', 'json', 'excel'], 
                                 help='Type of file to import')
        import_parser.add_argument('file_path', help='Path to the file to import')
        import_parser.add_argument('--preview', action='store_true', 
                                 help='Preview mode - validate without importing')
        import_parser.add_argument('--update-existing', action='store_true',
                                 help='Update existing articles (JSON only)')
        import_parser.add_argument('--es-host', default='localhost',
                                 help='Elasticsearch host (default: localhost)')
        import_parser.add_argument('--es-port', type=int, default=9200,
                                 help='Elasticsearch port (default: 9200)')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate files without importing')
        validate_parser.add_argument('file_type', choices=['csv', 'json', 'excel'],
                                   help='Type of file to validate')
        validate_parser.add_argument('file_path', help='Path to the file to validate')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Check if file exists
        if not Path(args.file_path).exists():
            self.logger.error(f"File not found: {args.file_path}")
            sys.exit(1)
        
        # Connect to Elasticsearch for import operations
        if args.command == 'import' and not args.preview:
            if not self.connect_elasticsearch(args.es_host, args.es_port):
                self.logger.error("Cannot proceed without Elasticsearch connection")
                sys.exit(1)
        
        # Execute command
        try:
            if args.command == 'import':
                if args.file_type == 'csv':
                    self.import_csv(args.file_path, args.preview)
                elif args.file_type == 'json':
                    self.import_json(args.file_path, args.preview, args.update_existing)
                elif args.file_type == 'excel':
                    self.import_excel(args.file_path, args.preview)
            
            elif args.command == 'validate':
                self.validate_file(args.file_path, args.file_type)
        
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    cli = ImportCLI()
    cli.run()


if __name__ == "__main__":
    main()
