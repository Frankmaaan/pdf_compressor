#!/bin/bash

# run.sh
# PDF compression tool quick start script

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color definition
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored text
print_colored() {
    echo -e "${1}${2}${NC}"
}

# Show usage help
show_help() {
    print_colored $BLUE "PDF compression tool quick start script"
    echo ""
    echo "Usage: ./run.sh [options] [PDF file or directory]"
    echo ""
    echo "options:"
    echo " -h, --help display this help message"
    echo "-c, --check check dependency tools"
    echo "-i, --install install dependent tools"
    echo " -t, --test run test checks"
    echo " -s, --split allow splitting files"
    echo "-v, --verbose verbose output mode"
    echo " -o, --output DIR specifies the output directory (default: ./output)"
    echo " --target-size SIZE target file size MB (default: 2.0)"
    echo " --max-splits NUM Maximum number of splits (default: 4)"
    echo ""
    echo "Example:"
    echo " ./run.sh document.pdf # Compress a single file"
    echo " ./run.sh -s document.pdf # Compress and allow splitting"
    echo " ./run.sh -o ./processed ./pdf_folder # Batch processing directory"
    echo " ./run.sh -v -s --target-size 8 big.pdf # Verbose mode, 8MB target"
    echo ""
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_colored $RED "Error: Python not found. Please install Python 3.7+."
        exit 1
    fi
}

# Check if main.py exists
check_main_script() {
    if [ ! -f "main.py" ]; then
        print_colored $RED "Error: main.py file not found. Please make sure you are running this script in the correct directory."
        exit 1
    fi
}

# Parse command line parameters
parse_arguments() {
    OUTPUT_DIR="./output"
    ALLOW_SPLITTING=""
    VERBOSE=""
    TARGET_SIZE=""
    MAX_SPLITS=""
    INPUT_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_python
                check_main_script
                print_colored $BLUE "Check dependency tools..."
                $PYTHON_CMD main.py --check-deps
                exit $?
                ;;
            -i|--install)
                print_colored $BLUE "Run dependency installation script..."
                if [ -f "install_dependencies.sh" ]; then
                    chmod +x install_dependencies.sh
                    ./install_dependencies.sh
                else
                    print_colored $RED "Error: install_dependencies.sh file not found"
                    exit 1
                fi
                exit $?
                ;;
            -t|--test)
                check_python
                print_colored $BLUE "Run test check..."
                $PYTHON_CMD test_tool.py
                exit $?
                ;;
            -s|--split)
                ALLOW_SPLITTING="--allow-splitting"
                shift
                ;;
            -v|--verbose)
                VERBOSE="--verbose"
                shift
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --target-size)
                TARGET_SIZE="--target-size $2"
                shift 2
                ;;
            --max-splits)
                MAX_SPLITS="--max-splits $2"
                shift 2
                ;;
            -*)
                print_colored $RED "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$INPUT_FILE" ]; then
                    INPUT_FILE="$1"
                else
                    print_colored $RED "Error: Only one input file or directory can be specified"
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# Verify input file
validate_input() {
    if [ -z "$INPUT_FILE" ]; then
        print_colored $RED "Error: Please specify the input PDF file or directory"
        echo ""
        show_help
        exit 1
    fi
    
    if [ ! -e "$INPUT_FILE" ]; then
        print_colored $RED "Error: input file or directory does not exist: $INPUT_FILE"
        exit 1
    fi
}

# Main execution function
main() {
    check_python
    check_main_script
    parse_arguments "$@"
    
    if [ -z "$INPUT_FILE" ]; then
        show_help
        exit 0
    fi
    
    validate_input
    
    # Build command
    CMD="$PYTHON_CMD main.py --input \"$INPUT_FILE\" --output-dir \"$OUTPUT_DIR\""
    
    if [ -n "$ALLOW_SPLITTING" ]; then
        CMD="$CMD $ALLOW_SPLITTING"
    fi
    
    if [ -n "$VERBOSE" ]; then
        CMD="$CMD $VERBOSE"
    fi
    
    if [ -n "$TARGET_SIZE" ]; then
        CMD="$CMD $TARGET_SIZE"
    fi
    
    if [ -n "$MAX_SPLITS" ]; then
        CMD="$CMD $MAX_SPLITS"
    fi
    
    # Display the commands to be executed
    print_colored $BLUE "Execute command:"
    print_colored $YELLOW "$CMD"
    echo ""
    
    #Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    #Execute command
    eval $CMD
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_colored $GREEN "✅ Processing completed!"
        print_colored $GREEN "Output file location: $OUTPUT_DIR"
    else
        print_colored $RED "❌ Processing failed (exit code: $exit_code)"
        print_colored $YELLOW "Please check the error message or view the log file: logs/process.log"
    fi
    
    exit $exit_code
}

# Set the script to be executable
chmod +x "$0"

#Run the main function
main "$@"