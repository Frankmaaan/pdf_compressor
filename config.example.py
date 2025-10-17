# config.example.py
# Configuration file example - can be copied as config.py and modified as needed

"""
PDF compression tool configuration file

This file contains various configuration options for the tool.
Copy this file as config.py and modify the parameters as needed.
"""

# =============================================================================
# Compression strategy configuration
# =============================================================================

# Customize compression strategy (if you don’t want to use the default strategy)
CUSTOM_STRATEGIES = {
    # You can add a custom compression parameter sequence
    # Format: Level -> Parameter List
    # 1: {
    # "name": "Custom high quality",
    #     "params_sequence": [
    #         {'dpi': 350, 'bg_downsample': 1},
    #         {'dpi': 300, 'bg_downsample': 2},
    #         # ...
    #     ]
    # }
}

# Quality bottom line setting
MIN_DPI = 100 # Minimum acceptable DPI value
MAX_BG_DOWNSAMPLE = 6 # Maximum background downsampling multiple

# =============================================================================
#File processing configuration
# =============================================================================

#Default target size (MB)
DEFAULT_TARGET_SIZE = 2.0

#Default maximum number of splits
DEFAULT_MAX_SPLITS = 4

# Temporary file cleanup
AUTO_CLEANUP_TEMP = True # Whether to automatically clean up temporary files
TEMP_DIR_PREFIX = "pdf_compressor_" # Temporary directory prefix

# =============================================================================
#OCR configuration
# =============================================================================

# Tesseract language settings
OCR_LANGUAGES = {
    'chinese': 'chi_sim', # Simplified Chinese
    'chinese_traditional': 'chi_tra', # Traditional Chinese
    'english': 'eng', # English
    'mixed': 'chi_sim+eng' # Mixed Chinese and English
}

#Default OCR language
DEFAULT_OCR_LANG = 'chi_sim'

# OCR processing options
OCR_CONFIG = {
    'psm': 1,  # Page Segmentation Mode
    'oem': 1,  # OCR Engine Mode
}

# =============================================================================
# Log configuration
# =============================================================================

# Log level
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

DEFAULT_LOG_LEVEL = 'INFO'

# Log file settings
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 3 # Number of log files retained

# =============================================================================
#Performance optimization configuration
# =============================================================================

# Concurrent processing settings (may be supported in future versions)
MAX_PARALLEL_JOBS = 1 # The current version only supports single thread

#Memory usage limit
MAX_MEMORY_USAGE_MB = 1024 # Maximum memory usage (MB)

# Timeout settings
COMMAND_TIMEOUT = 300 # Maximum execution time of a single command (seconds)
TOTAL_PROCESS_TIMEOUT = 1800 # Maximum processing time of a single file (seconds)

# =============================================================================
# Advanced parameter configuration
# =============================================================================

# recode_pdf advanced parameters
RECODE_PDF_ADVANCED = {
    'fg_slope': None, # Foreground layer slope, None means use the default value
    'bg_slope': None, # Background layer slope, None means use the default value
    'mask_compression': 'jbig2', #Mask compression algorithm: jbig2 or ccitt
    'jpeg_quality': None, #JPEG quality, None means use the default value
}

# pdftoppm advanced parameters
PDFTOPPM_ADVANCED = {
    'aa': True, # Enable anti-aliasing
    'aaVector': True, # Enable vector anti-aliasing
    'forceNum': False, # Force numeric page number
}

# =============================================================================
#File filtering configuration
# =============================================================================

#Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.PDF', '.Pdf', '.pDf', '.pdF', '.PdF', '.PDf', '.pDF']

# File size limit
MIN_FILE_SIZE_MB = 0.1 # Minimum processing file size
MAX_FILE_SIZE_MB = 1000 # Maximum file size processed

# =============================================================================
# Output configuration
# =============================================================================

# Output file naming
OUTPUT_NAMING = {
    'compressed_suffix': '_compressed', # Compressed file suffix
    'part_prefix': '_part', # Split file prefix
    'timestamp_format': '%Y%m%d_%H%M%S', # Timestamp format
}

# Whether to retain original file information
PRESERVE_METADATA = True

# =============================================================================
# Error handling configuration
# =============================================================================

# Retry configuration
MAX_RETRIES = 2 # Maximum number of retries
RETRY_DELAY = 5 # Retry interval (seconds)

# Error handling strategy
ERROR_HANDLING = {
    'continue_on_error': True, # Whether to continue processing other files when an error is encountered
    'save_error_report': True, # Whether to save the error report
    'detailed_traceback': False, # Whether to include detailed error tracing in the log
}

# =============================================================================
# Development and debugging configuration
# =============================================================================

#Debug mode
DEBUG_MODE = False

# Whether to keep intermediate files (for debugging)
KEEP_INTERMEDIATE_FILES = False

#Performance analysis
ENABLE_PROFILING = False

# Detailed command output
VERBOSE_COMMANDS = False