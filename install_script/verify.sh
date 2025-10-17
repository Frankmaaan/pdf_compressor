#!/bin/bash

# ==============================================================================
# archive-pdf-tools Final function verification script (verify.sh) - qpdf version
# ------------------------------------------------------------------------------
# Function: Verify that Grok, OpenJPEG, and qpdf can work normally.
# ==============================================================================

# --- Configuration ---
all_ok=true
test_dir=""
export PATH="$PATH:$HOME/.local/bin" # Make sure the pipx command is available
# Correct the parameter order of jbig2enc to solve the WSL pipeline syntax problem
export RECODE_PDF_JBIG2ENC_ARGS="--output-file={output} {input}" 

# --- Helper function (for color output) ---
print_info() { echo -e "\n\e[34m==> $1\e[0m"; }
print_success() { echo -e "  \e[32m✔ $1\e[0m"; }
print_error() { echo -e "  \e[31m✖ $1\e[0m"; }
print_step() { echo -e "  - $1"; }
# Centrally handle verification failures and keep files
handle_failure() {
    print_error "💥 Function verification failed. Please check the log above carefully."
    print_info "Keep temporary files for debugging..."
    echo "The temporary file is located at: $test_dir"
    cd ~ # Return to the home directory
    exit 1
}

# --- Script starts ---
echo "============================================================"
echo "Start archive-pdf-tools functional verification test (qpdf dual tool verification)..."
echo "============================================================"

# --- Step 1: Verify all installed tools ---
print_info "Step 1/5: Verify all installed key tool commands..."

print_step "Check key dependency commands..."
# Grok, OpenJPEG, qpdf, recode_pdf
tools=("pdftoppm" "tesseract" "jbig2" "grk_compress" "opj_compress" "qpdf" "recode_pdf")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        print_success "$tool command found ($tool)."
    else
        print_error "$tool command not found!"
        all_ok=false
    fi
done

if [ "$all_ok" = false ]; then
    print_error "\nBasic command check failed and workflow testing cannot continue."
    handle_failure
fi

# --- Step 2: Prepare test file (create a two-page PDF) ---
print_info "Step 2/5: Prepare end-to-end workflow test file (create 2-page PDF)..."
test_dir=$(mktemp -d)
cd "$test_dir"
print_step "Create a test file in the temporary directory: $test_dir"

# Create a PDF containing two pages of text
echo -e "Page 1" > page1.txt
echo -e "\n\n\nPage 2" > page2.txt # Make sure it is a separate page
enscript -o temp.ps page1.txt page2.txt &> /dev/null
ps2pdf temp.ps test_2page.pdf &> /dev/null
rm -f temp.ps page1.txt page2.txt

if ! [ -s "test_2page.pdf" ]; then print_error "Failed to create 2 page PDF!"; handle_failure; fi
print_success "Successfully created 2-page test PDF (test_2page.pdf)."

# Continue to create a single-page recode input file
pdftoppm -png -r 300 test_2page.pdf test_page &> /dev/null
tesseract test_page-1.png test_hocr -l eng hocr &> /dev/null
print_success "Successfully created PNG and hOCR files required for recode."


# --- Step 3: Verify Grok Compression ---
print_info "Step 3/5: Verify Grok (grk_compress) compression functionality..."
RECODE_CMD_GROK="timeout 1m recode_pdf -v --from-imagestack 'test_page-1.png' --hocr-file 'test_hocr.hocr' --dpi 300 --mask-compression jbig2 -J grok -o 'compressed_grok.pdf'"

print_step "Perform Grok compression test..."
eval $RECODE_CMD_GROK &> recode_grok_log.txt
if [[ ${PIPESTATUS[0]} -ne 0 ]] && [[ ${PIPESTATUS[0]} -ne 124 ]]; then # Make sure to check the exit status of the eval command
    print_error "(Grok test) Compression failed (exit code: ${PIPESTATUS[0]})!"
    all_ok=false
elif ! [ -s "compressed_grok.pdf" ]; then
    print_error "(Grok Test) Compression timed out or failed!"
    all_ok=false
else
    print_success "(Grok test) Successfully created compressed PDF (compressed_grok.pdf)."
fi


# --- Step 4: Verify OpenJPEG compression ---
print_info "Step 4/5: Verify OpenJPEG (opj_compress) compression capabilities..."
RECODE_CMD_OPENJPEG="timeout 1m recode_pdf -v --from-imagestack 'test_page-1.png' --hocr-file 'test_hocr.hocr' --dpi 300 --mask-compression jbig2 -J openjpeg -o 'compressed_openjpeg.pdf'"

print_step "Perform OpenJPEG compression test..."
eval $RECODE_CMD_OPENJPEG &> recode_openjpeg_log.txt
if [[ ${PIPESTATUS[0]} -ne 0 ]] && [[ ${PIPESTATUS[0]} -ne 124 ]]; then
    print_error "(OpenJPEG test) Compression failed (exit code: ${PIPESTATUS[0]})!"
    all_ok=false
elif ! [ -s "compressed_openjpeg.pdf" ]; then
    print_error "(OpenJPEG test) Compression timed out or failed!"
    all_ok=false
else
    print_success "(OpenJPEG test) Successfully created compressed PDF (compressed_openjpeg.pdf)."
fi


# --- Step 5: Verify qpdf splitting function ---
print_info "Step 5/5: Verify qpdf PDF splitting functionality..."
print_step "Using qpdf to split test_2page.pdf..."

# Try to split the second page
qpdf --empty --pages test_2page.pdf 2 -- split_page2.pdf 2>/dev/null

if [ -s "split_page2.pdf" ]; then
    print_success "(qpdf test) Successfully split PDF into split_page2.pdf."
else
    print_error "(qpdf test) Split PDF failed!"
    all_ok=false
fi


# --- Final summary and cleanup ---
if [ "$all_ok" = true ]; then
    print_info "Clean up temporary verification files..."
    rm -rf "$test_dir"
    echo "============================================================"
    echo -e "\e[32m🎉 All verifications are successful! All tools can work normally.\e[0m"
    echo "============================================================"
    cd ~ # Return to the home directory
else
    handle_failure
fi
