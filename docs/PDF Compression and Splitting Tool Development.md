

# **Research report on automatic compression and splitting strategies for professional title declaration PDF files based on archive-pdf-tools**

## **Part 1: Executive Summary and Basic Concepts**

This report aims to provide a technical solution for a specific professional title application. The core goal is to develop a Python-based command line tool for automated compression and splitting of PDF files in the WSL/Ubuntu 24.04 environment. This tool is designed to ensure that all submitted PDF files meet the hard size limit of less than 2MB, while maximizing file quality where possible and, where necessary, splitting individual files into up to four parts that meet the size limit.

### **1.1 Project tasks and strategic goals**

The core task of the project is to create an automated auxiliary tool to cope with the strict requirements for PDF attachments in professional title applications. Specific needs can be summarized as follows:

* **Core Features**: Compress input single or batch PDF files to the specified size (default is 2MB).  
* **Input method**: Supports single file path and entire directory as input.  
* **Layered Strategy**: Based on the size of the source file, different compression strategies are adopted to balance file quality and size.  
* **Split mechanism**: When a single file cannot be compressed to the target size within an acceptable quality range, automatically split it into multiple (up to four) files that meet the size requirements.  
* **Technology stack**: The project is specified in the WSL/Ubuntu 24.04 environment, using the recode\_pdf command in the archive-pdf-tools tool set as the core compression engine.

### **1.2 Core technology clarification: recode\_pdf is used as a reconstruction engine rather than a compression tool**

Before diving into specific strategies, a key concept about the core tool recode_pdf must be clarified. Preliminary analysis of the project believes that recode\_pdf is a direct PDF compression tool, that is, inputting a PDF and outputting a smaller PDF. However, a closer look at how it works reveals that this understanding isn't entirely accurate. The essence of recode\_pdf is a **PDF reconstruction engine**, not a simple file compressor 1.

Its main workflow is not to directly modify the input PDF, but to build a new, highly optimized PDF file from scratch based on a set of raster images (such as TIFF, JPEG2000) and an hOCR file containing text content and coordinate information. recode\_pdf uses Mixed Raster Content (MRC) compression technology to separate the page into a high-resolution foreground layer (text, lines) and a low-resolution background layer (pictures, gradients), thereby achieving an extremely high compression rate 1.

Although recode\_pdf provides a --from-pdf option, which seems to be able to process PDF directly, its official documentation clearly states that this function is "not well tested", and its stability and effect cannot be guaranteed when processing PDFs that contain multiple images or complex layouts per page. 1. Therefore, for a productivity tool that requires stability and reliability, relying on this experimental feature is not advisable.

### **1.3 "Deconstruction-Analysis-Reconstruction" (DAR) three-stage processing process**

Based on a correct understanding of how recode\_pdf works, a robust solution must adopt a multi-stage processing flow. This report proposes a three-stage architecture called "Deconstruct-Analyze-Reconstruct" (DAR) as the technical cornerstone of the entire project.

1. **Deconstruction**: The goal of this stage is to convert each page of the source PDF into a high-quality raster image. This is the basis for all subsequent processing. The resolution and format of the image will directly affect the quality of the final output.  
2. **Analysis**: At this stage, optical character recognition (OCR) is performed on the deconstructed image and a file in hOCR (HTML-based OCR) format is generated. hOCR files not only contain recognized text, but also accurately record the positional coordinates of each character, word and line, which is key to reconstructing searchable, copyable text layers1.  
3. **Reconstruction**: This is the last and most core stage. Use the recode\_pdf command to take the image sequence and hOCR file generated in the first two stages as input, and use MRC technology to reconstruct a new, highly compressed PDF file that complies with PDF/A and PDF/UA standards 1.

Although this DAR process is more complex than direct compression and involves more intermediate steps and dependent tools, it is fully consistent with the design philosophy of recode\_pdf and can maximize its compression potential and ensure the quality and compliance of the output files. This architectural change means that the project needs to manage not only recode\_pdf itself, but a complete processing chain composed of multiple command line tools.

### **1.4 Report Structure and Navigation**

The subsequent parts of this report will focus on the DAR architecture, from the in-depth analysis of the tool chain to the design of the core algorithm, to the specific Python implementation blueprint, and finally discuss advanced tuning techniques and project summary. The report will systematically explain how to build a powerful and reliable automation tool that can meet all needs.

## **Part 2: In-depth analysis of the core tool chain**

Implementing the DAR process requires a tool chain that works together. This section will provide a detailed technical review of each of the key command line tools that make up the process, clarifying its role in the process, the rationale for choosing that tool, and diving into the commands and parameters directly relevant to this project.

### **2.1 Deconstruction phase: pdftoppm (from poppler-utils)**

* **Role**: In the first stage of the DAR process, pdftoppm is responsible for converting input PDF files into raster images page by page. These images are the only source of material for subsequent OCR analysis and final PDF reconstruction.  
* **Reason for selection**: Among many PDF to image conversion tools (such as pdfimages or Ghostscript), pdftoppm was selected for its precise control over output parameters. In particular, its -r parameter allows you to directly specify the DPI (dots per inch) of the output image, which is crucial for controlling the initial balance of image quality and file size. In addition, it supports multiple output formats (such as TIFF, PNG, JPEG), among which the TIFF format is an ideal choice for high-quality OCR due to its lossless compression characteristics.  
* **Key command syntax**:
  * **Basic usage**: pdftoppm \-tiff \-r 300 input.pdf output\_prefix
  * **Detailed explanation of parameters**:
    * \-tiff: Specify the output format as TIFF. The TIFF format can preserve image information losslessly and ensure the accuracy of OCR.  
    * \-r \<dpi\>: Set the resolution of the output image. This is the first lever to control quality and size. A higher initial value (such as 300 DPI) is the basis for ensuring text clarity 3.  
    * input.pdf: source PDF file.  
    * output\_prefix: The prefix of the output image file. pdftoppm will automatically generate files with serial numbers for each page, such as output\_prefix-01.tif, output\_prefix-02.tif, etc.

### **2.2 Analysis phase: tesseract OCR engine**

* **Role**: During the analysis phase, tesseract is responsible for processing the images generated by pdftoppm and extracting text information. Its key task is to generate hOCR files necessary for recode\_pdf.  
* **Reason for selection**: Tesseract is one of the most advanced and widely used open source OCR engines currently maintained by Google. It supports multiple languages ​​and is able to output hOCR format. hOCR is an open standard based on HTML that not only contains recognized text, but also accurately marks the bounding box coordinates of text blocks, paragraphs, lines, words and characters through HTML tags 4. These precise coordinate information are the basis for recode\_pdf's ability to perfectly overlay text layers on top of background images to generate searchable PDFs 1.  
* **Key command syntax**:
  * **Basic usage**: tesseract input\_image.tif output\_hocr \-l chi\_sim hocr
  * **Detailed explanation of parameters**:
    * input\_image.tif: input single page image file.  
    * output\_hocr: output hOCR file name prefix (.hocr extension will be added automatically).  
    * \-l \<lang\>: Specify the recognition language. For Chinese documents, chi\_sim (Simplified Chinese) or chi\_tra (Traditional Chinese) should be used.  
    * hocr: Specify the output format as hOCR.

### **2.3 Reconstruction phase: recode\_pdf (from archive-pdf-tools)**

* **Role**: As the last link of the DAR process, recode\_pdf is the core to achieve high compression rate. It receives image sequences and hOCR files and uses MRC technology to generate the final PDF file.  
* **MRC Technology Introduction**: The Mixed Raster Content (MRC) model is an advanced image segmentation and compression technology. It intelligently breaks down a page of content into three parts:
  1. **Background Layer**: Contains all color images, photos, and gradient backgrounds on the page. This layer is usually heavily downsampled and uses lossy compression (such as JPEG2000) because it requires less visual detail1.  
  2. **Foreground Layer**: Contains high-frequency information such as text and line art. This layer also typically uses lossy compression, but at a relatively higher resolution.  
  3. Binary Mask Layer: This is a high-resolution black and white image that precisely defines which pixels in the foreground layer are visible (i.e. the shape of text and lines). This layer uses a lossless compression algorithm (such as JBIG2 or CCITT G4) to ensure the sharpness of text edges 1.  
     recode\_pdf superimposes these three layers in the final PDF page, thereby greatly compressing the size of the background image while maintaining extremely high definition of the text, achieving a significant reduction in the overall file size.  
* **In-depth analysis of key parameters**:
  * \--dpi \<int\>: Specify the resolution of the input image. This value should be consistent with the DPI used by pdftoppm when generating the image. It directly determines the base resolution of the mask layer and foreground layer, and is the most important parameter affecting text clarity1.  
  * \--bg-downsample \<int\>: Background layer downsampling factor. This is a key parameter that controls file size. A value of N means that the background layer's resolution will be reduced to dpi/N. For example, --dpi 300 and --bg-downsample 3 will make the background layer have an effective resolution of 100 DPI, while the foreground text remains sharp at 300 DPI. This is the most effective way to reduce file size without sacrificing text readability1.  
  * \--mask-compression \<jbig2|ccitt\>: Specify the compression algorithm of the mask layer. jbig2 offers higher lossless compression than ccitt, but has some history of patent issues (although most have expired). ccitt (often referred to as CCITT Group 4) is a widely supported and patent-free fax compression standard that offers slightly less effective compression than jbig2 6 as an alternative.  
  * \--from-imagestack '\<glob\>': Specifies the input image file sequence. It accepts a glob pattern, such as 'temp\_dir/page-\*.tif', to match all page images 1.  
  * \--hocr-file \<file\>: Specify the hOCR file generated by tesseract.

### **2.4 Emergency plan: qpdf is used for PDF splitting and processing**

* **Role**: When all compression attempts fail to compress the file to the target size above the quality baseline, qpdf will serve as an emergency tool, responsible for precise page splitting of PDF files.  
* **Reason for selection**: In the Linux command line environment, there are many tools that can handle PDF splitting, such as pdftk, Ghostscript and pdfseparate. The choice of qpdf is based on the following comprehensive considerations:
  * **Modern and Active**: qpdf is a project that is still actively developed and maintained, and is compatible with the latest versions of many Linux distributions.  
  * **Official repository support**: qpdf is part of the Ubuntu 24.04 standard software sources and is easy to install (sudo apt install qpdf). In contrast, pdftk has been removed from the official sources of many mainstream distributions and needs to be installed via snap or compiled Java version, increasing deployment complexity 7.  
  * **Powerful syntax**: qpdf provides a very clear and powerful page selection syntax, which can easily extract arbitrary page ranges from one or more files and generate new PDF files, which is exactly what this project split logic requires 7.  
  * **Performance**: While pdftk or Ghostscript may be faster in some specific scenarios, qpdf excels at content preservation and metadata handling, and its performance is completely adequate for the file sizes and operations involved in this project. 8.  
* **Key command syntax**:
  * **Extract page range**: qpdf input.pdf \--pages. \<start\>-\<end\> \-- output.pdf
  * **Detailed explanation of parameters**:
    * \--pages. \<start\>-\<end\>: This is the core of qpdf page selection. . represents the input file itself to avoid repeatedly writing the file name. \<start\>-\<end\> defines the page range to be extracted (including the beginning and the end).  
    * \--: delimiter to clearly separate page selection parameters from output file names 7.  
  * **Example**: To extract pages 1 to 10 from a file named document.pdf and generate part1.pdf, the command is: qpdf document.pdf \--pages. 1-10 \-- part1.pdf.

### **Table 1: Analysis of core tool chain components**

| Tool name | Software package to which it belongs | Main role in the process | Key commands/parameters | Example usage |
| :---- | :---- | :---- | :---- | :---- |
| pdftoppm | poppler-utils | **Deconstruction**: Convert PDF pages to raster images | \-r \<dpi\>, \-tiff, \-png | pdftoppm \-tiff \-r 300 in.pdf out\_prefix |
| tesseract | tesseract-ocr | **Analysis**: OCR from image and generate hOCR file | \<input\> \<output\>, \-l \<lang\>, hocr | tesseract page-01.tif page-01 \-l chi\_sim hocr |
| recode\_pdf | archive-pdf-tools | **Reconstruct**: Reconstruct highly compressed PDF based on images and hOCR | \--from-imagestack, \--hocr-file, \--dpi, \--bg-downsample | recode\_pdf \--from-imagestack 'imgs/\*.tif' \--hocr-file data.hocr \--dpi 300 \--bg-downsample 3 \-o out.pdf |
| qpdf | qpdf | **Emergency Split**: Split PDF by page number when compression fails | \--pages. \<start\>-\<end\> \-- | qpdf in.pdf \--pages. 1-10 \-- part1.pdf |

## **Part 3: Core Algorithm: Hierarchical Strategy and Iterative Optimization**

The “intelligence” of this project is reflected in its core algorithm, which converts user-defined hierarchical requirements into a deterministic, executable program logic. It not only defines strategies for handling files of different sizes, but also designs an iterative optimization loop to find the best balance between quality and size.

### **3.1 Define processing levels**

Depending on the size of the input PDF file (denoted as ), the algorithm classifies the file into one of the following four processing levels:

* **Level 0 (ignored)**: If , the file meets the requirements, no processing is required, and it is skipped directly.  
* **Level 1 (High Quality Compression)**: If the size of this type of file is not large, the compression goal is to reduce the file size to less than 2MB while ensuring the highest quality. The algorithm will start at very high quality settings with minimal parameter adjustments.  
* **Level 2 (Balanced Compression)**: If , these files are of moderate size. The main goal is still to compress to under 2MB without splitting. But unlike level 1, the algorithm will reduce quality parameters more aggressively, triggering a split mechanism if the final quality drops to an unacceptable level.  
* **Level 3 (Extreme Compression)**: If , these files are very large. Since the limits of 2MB and splitting up to 4 files are hard requirements, the algorithm will have the primary goal of meeting these limits, with quality becoming a secondary consideration. The compression strategy will be very aggressive and a split plan will likely be initiated directly.

### **3.2 Iterative optimization loop: heuristic search to find optimal parameters**

In order to find the most suitable compression parameters for each file, this program designs an iterative optimization loop. This is not a time-consuming brute force search, but a guided descent process from high quality to low quality, aiming to find a parameter combination that meets the conditions in the least number of attempts.

**Algorithm Process Overview**:

1. **Initialization**: Select an initial set of high-quality parameters based on the level to which the file belongs. For example, for level 1 files, you can start with dpi=300, bg-downsample=1.  
2. **Execute DAR process**: Use the current parameter set to completely execute the "deconstruction-analysis-reconstruction" process and generate a temporary output PDF file.  
3. **Check condition**: Get the size of the output file and compare it with the target size (2MB).  
4. **Determine success/failure**:
   * **Success**: If the output file size is less than or equal to the target size, it is considered that suitable parameters have been found. The loop terminates and the file is processed.  
   * **Failure**: If the output file is still too large, you need to reduce the quality parameters and go to the next step.  
5. **Parameter Downgrade Strategy**: Parameter reduction follows a predefined sequence aimed at minimizing quality loss.  
   * **Prioritize increasing background downsample (bg-downsample)**: First, gradually increase the value of bg-downsample (for example, from 1 to 2, then to 3, up to 4 or 5). This step usually results in significant file size reduction with minimal impact on text clarity, since only the quality of the background image is reduced1.  
   * **Secondly reduce the resolution (dpi)**: When bg-downsample reaches its upper limit (or the effect of continuing to increase is not obvious), start to gradually reduce the dpi value (for example, from 300 DPI to 250 DPI, and then to 200 DPI). Lowering the DPI will affect both the foreground and the background, which will have a more direct impact on the text quality, so it is placed in the second step 3.  
6. **Loop or Exit**: Use the new parameter set, return to step 2, and repeat the entire process. If the parameters have been reduced to the preset "quality bottom line" and still cannot meet the size requirements, the loop is terminated and the compression is determined to have failed.

### **3.3 Define quality bottom line**

In order to prevent the algorithm from endlessly reducing quality and producing unreadable output files, a "quality bottom line" must be set. This bottom line is mainly reflected by setting a minimum acceptable DPI value, for example, min\_dpi=150. 150 DPI is generally considered the minimum acceptable resolution for screen reading and non-high-quality printing 3.

When the dpi parameter in the iterative optimization loop is reduced to this value and bg-downsample has reached the upper limit, but the generated file size still exceeds the standard, the algorithm will stop further compression attempts. At this time, for files configured to allow splitting, the next stage of the emergency splitting protocol will be triggered.

### **Table 2: Layered compression strategy matrix**

The following table embodies the above-mentioned hierarchical logic and iteration strategy, forming a clear parameter matrix that can be directly used for programming implementation.

| Input size hierarchy | Primary target | Initial dpi | Initial bg-downsample | Parameter iteration order | Quality bottom line (min\_dpi) | Action after compression failure |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Level 1** (2-10MB) | Highest possible quality | 300 | 1 | 1\. Increase bg-downsample (to 3) 2\. Decrease dpi (to 200) | 200 | Trigger splitting |
| **Level 2** (10-50MB) | Prioritize no splitting | 300 | 2 | 1\. Increase bg-downsample (to 4) 2\. Decrease dpi (to 150) | 150 | Trigger splitting |
| **Level 3** (\>50MB) | Meet size and split number limits | 200 | 3 | 1\. Increase bg-downsample (to 5) 2\. Decrease dpi (to 150) | 150 | Force split (acceptable quality loss) |

## **Part 4: Emergency Protocol: PDF Splitting Logic**

When a file, after iterative compression, still cannot meet the size requirements above the quality baseline, the emergency split protocol is activated. This is the last line of defense to ensure that all documents are ultimately submitted.

### **4.1 Trigger conditions for split**

The starting condition of the splitting protocol is very clear: if and only if the iterative compression loop described in Part 3 is terminated because the quality bottom line (min\_dpi) is reached, and the final generated PDF file size still exceeds 2MB.

This triggering mechanism has different meanings for files at different levels:

* For **Level 1 and Level 2** files, triggering splitting is to **protect quality** and avoid generating documents with too low resolution.  
* For **Level 3** files, splitting is triggered because even at the lowest quality settings, **the size of a single file cannot be compressed below 2MB**.

### **4.2 Calculate split point**

The core constraint for splitting is a maximum of 4 parts. The algorithm needs to intelligently decide the optimal number of splits (denoted as , where ).

* Initial strategy: average allocation based on page number
  For a PDF with a total number of pages N, the algorithm will first try the simplest k=2 splitting solution:
  * Part 1: Page 1 to Page
  * Part Two: Page to Page
* Introduce predictive splitting heuristic algorithm
  A simple even distribution strategy may be inefficient. For example, after a 100MB file is split into two 50MB parts, each part is still much larger than the compression target. If you directly perform a complete and time-consuming DAR compression process on one of the parts, the result is likely to be failure. This will waste a lot of computing resources.  
  To optimize this process, a **predictive splitting heuristic** can be introduced. This algorithm estimates a more reasonable initial number of splits based on the original file size.  
  * Heuristic rules: You can set an experience threshold. For example, it is considered that a 25MB PDF block is more likely to be compressed to 2MB. Then the initial split number can be calculated like this:

  * **Application**: For a 100MB file, this formula would suggest . The algorithm will try a 4-way split directly instead of starting with a 2-way split, greatly improving efficiency. For a 30MB file, the formula suggests, the algorithm will start with a 2-way split.

### **4.3 Iterative splitting and processing**

The splitting process itself is also an iterative verification process:

1. **Select the number of splits k**: Determine an initial number of splits based on the heuristic algorithm in the previous section.  
2. **Generate subdocuments**: Use qpdf to split the original PDF according to the page number range and generate a temporary PDF subdocument.  
3. **Verify the first subdocument**: Select the first subdocument (for example, the part with page numbers ranging from to ), and perform a complete DAR compression process on it using the most aggressive parameters (for example, dpi=150, bg-downsample=4).  
4. **Evaluation results**:
   * **Success**: If the first subdocument is successfully compressed to less than 2MB, then you can be optimistic that other subdocuments of similar size will also be successful. At this point, the script continues processing the remaining subdocuments.  
   * **Failure**: If even the first subdocument cannot be compressed up to standard, it means that the current splitting granularity is still too large. The algorithm will increase the number of splits () as long as , return to step 2, regenerate smaller subdocuments and verify again.  
5. **Final processing**: Once a feasible number of splits is found so that all sub-documents can be successfully compressed, the entire split process is declared successful. If the attempt still fails, it is reported that the file processing failed and manual intervention is required.

### **4.4 File Management after Split**

After successful splitting and compression, the script must take care of clear management of output files and temporary files.

* **Naming convention**: Multiple output files need to have logical and clear names so that users can understand their order. For example, for the source file mydocument.pdf, the split files should be named mydocument\_part1.pdf, mydocument\_part2.pdf,...  
* **Temporary file cleaning**: During the entire splitting and compression process, a large number of temporary files will be generated, including:
  * Uncompressed PDF subdocument generated by qpdf.  
  * All page images deconstructed from each subdocument.  
  * hOCR files generated for each subdocument.  
    The script must ensure that after processing a file (regardless of success or failure), all related temporary files are completely deleted to avoid taking up unnecessary disk space.

## **Part 5: Python Implementation Blueprint**

This section will provide a specific software engineering guide for building this PDF processing tool. The content includes recommended project structure, command line interface design, and pseudocode implementation of core logic.

### **5.1 Recommended project structure**

A clear, modular project structure is essential for code maintainability and scalability. The following structure is recommended:

pdf-compressor/  
├── main.py \# Main program entry, responsible for parsing command line parameters and distributing tasks
├── compressor/  
│   ├── \_\_init\_\_.py  
│ ├── pipeline.py \# Encapsulates the complete DAR processing flow
│ ├── strategy.py \# Implement hierarchical strategy and iterative optimization loop
│ ├── splitter.py \# Implement PDF splitting logic
│ └── utils.py \# Contains auxiliary functions, such as file size acquisition, temporary file management, etc.
├── tests/ \# unit test directory
└── README.md \# Project description document

This structure separates different functional logic into different modules, making the code easier to understand and test.

### **5.2 Command Line Interface (CLI) Design**

A powerful and user-friendly command line interface can be easily built using the argparse module in the Python standard library.

**Designed CLI parameters**:

* \--input \<path\> (required): Specify the input source path, which can be a PDF file or a directory containing PDF files.  
* \--output-dir \<path\> (required): Specify the directory where the processed files are stored.  
* \--target-size \<int\> (optional): Specify the target file size in MB. The default value is 2.  
* \--allow-splitting (optional): A boolean flag. If this parameter is provided, allows splitting to be enabled if compression fails. The default is not enabled.  
* \--max-splits \<int\> (optional): Maximum number of splits allowed. The default value is 4.

**Example call**:

Bash

\# Process a single file, allowing splitting
python main.py \--input /path/to/large.pdf \--output-dir /path/to/output \--allow-splitting

\# Process the entire directory, using default settings
python main.py \--input /path/to/source\_folder \--output-dir /path/to/output

### **5.3 Core logic pseudo code**

The following pseudocode outlines the implementation logic of the core module of the program and can be used as a direct reference for writing Python code.

#### **Main logic of main.py**

Python

function main():  
    args \= parse\_command\_line\_arguments()

    if is\_directory(args.input):  
        pdf\_files \= find\_pdfs\_in\_directory(args.input)  
        for pdf\_file in pdf\_files:  
            process\_file(pdf\_file, args)  
    else:  
        process\_file(args.input, args)

#### **File processing logic of pipeline.py**

Python

function process\_file(file\_path, args):  
    original\_size\_mb \= get\_file\_size\_in\_mb(file\_path)

    if original\_size\_mb \< args.target\_size:  
        print(f"Skipping {file\_path}, already meets size requirement.")  
        \# Optionally, copy the file to the output directory  
        return

    tier \= determine\_tier(original\_size\_mb)  
    strategy\_params \= get\_strategy\_for\_tier(tier)

    \# Run iterative compression
    success, result\_path \= run\_iterative\_compression(file\_path, strategy\_params, args)

    if success:  
        print(f"Successfully compressed {file\_path} to {result\_path}")  
    elif args.allow\_splitting:  
        print(f"Compression failed for {file\_path}. Attempting to split.")  
        run\_splitting\_protocol(file\_path, strategy\_params, args)  
    else:  
        print(f"Compression failed for {file\_path}. Splitting not enabled.")

#### **Iteration compression logic of strategy.py**

Python

function run\_iterative\_compression(file\_path, strategy, args):  
    \# generate\_parameter\_sequence will generate a series of (dpi, bg\_downsample) combinations according to the policy
    for params in generate\_parameter\_sequence(strategy):  
        temp\_dir \= create\_temporary\_directory()  
        try:  
            \# 1\. Deconstruction: call pdftoppm
            image\_files \= deconstruct\_pdf\_to\_images(file\_path, temp\_dir, params.dpi)

            \# 2\. Analysis: Call tesseract
            hocr\_file \= analyze\_images\_to\_hocr(image\_files, temp\_dir)

            \# 3\. Reconstruction: call recode\_pdf
            output\_pdf\_path \= reconstruct\_pdf(image\_files, hocr\_file, temp\_dir, params)

            \# 4\. Check size
            if get\_file\_size\_in\_mb(output\_pdf\_path) \<= args.target\_size:  
                move\_file(output\_pdf\_path, args.output\_dir)  
                return (True, final\_path)  
        finally:  
            cleanup\_directory(temp\_dir)

    \# If the loop ends without success
    return (False, None)

### **5.4 Use the subprocess module to manage external processes**

The best practice for calling command line tools in Python is to use the subprocess module.

* **Recommended method**: Use the subprocess.run() function because it provides the most flexible and simplest interface.  
* **Key Parameters**:
  * check=True: If the called command returns a non-zero exit code (indicating an execution error), subprocess.run() will throw a CalledProcessError exception. This makes error handling simple and straightforward.  
  * capture\_output=True and text=True: Used to capture the standard output and standard error streams of commands to facilitate logging and debugging.  
* **Example**: Build a function that calls pdftoppm.

Python

import subprocess

def deconstruct\_pdf\_to\_images(pdf\_path, output\_dir, dpi):  
    command \= \[  
        "pdftoppm",  
        "-tiff",  
        "-r", str(dpi),  
        pdf\_path,  
        f"{output\_dir}/page"  \# output prefix  
    \]  
    try:  
        result \= subprocess.run(command, check=True, capture\_output=True, text=True)  
        \# Log result.stdout if needed  
        \#... find generated image files and return their paths  
    except subprocess.CalledProcessError as e:  
        print(f"Error during PDF deconstruction: {e.stderr}")  
        raise  \# Re-raise the exception to be handled by the caller

### **5.5 Error handling and temporary file management**

A robust tool must be able to handle exceptions appropriately and keep the system clean.

* **Use try...finally**: This is key to ensuring that temporary files and directories are always cleaned up. Regardless of whether the code in the try block executes successfully or throws an exception, the cleanup code in the finally block will be executed.  
* **Use the tempfile module**: Python's tempfile module can safely create temporary directories and files and is ideal for managing intermediate products. The tempfile.TemporaryDirectory() context manager can automatically clean up the directory when exiting the scope.  
* **Logging**: Use the logging module to record the processing progress of each file, the parameters used, the output of external commands, and any errors that occur. This is essential for debugging and tracking the status of batch processing tasks.

## **Part 6: Advanced Tuning and Conclusion**

This section summarizes the optimal strategies proposed in the report and provides guidance on advanced parameter tuning for users who wish to further explore the limits of quality and compression.

### **6.1 Summary of optimal strategies**

The optimal strategy proposed in this report is a systematic, multi-stage solution whose core is:

1. **Adopt "Deconstruction-Analysis-Reconstruction" (DAR) architecture**: This is the most reliable way to take advantage of the powerful compression capabilities of recode\_pdf, avoiding its unstable --from-pdf mode.  
2. **Implement hierarchical iterative optimization algorithm**: adopt compression strategies of different strengths according to file size, and intelligently find the best compression parameters through a heuristic search loop from high quality to low quality.  
3. **Integrated emergency splitting protocol based on qpdf**: When compression cannot meet the requirements, an efficient and reliable splitting mechanism is used as the final guarantee to ensure that all files can meet the submission specifications.

This combined strategy strikes a good balance between automation, efficiency and output quality, and is capable of assisting in job title declarations.

### **6.2 Advanced parameter tuning: Slope parameter**

In addition to dpi and bg-downsample, recode\_pdf also provides some lower-level parameters that can provide more fine-grained control over JPEG2000 compression quality. The most important of these is the "slope" parameter 6 of the foreground and background layers.

* **fg\_slope and bg\_slope**: These two parameters directly control the quantization level of the JPEG2000 encoder. The smaller the value, the higher the compression rate, but the greater the image quality loss. fg\_slope controls the foreground layer (mainly the pixels around the text), and bg\_slope controls the background layer.  
* **Tuning Scenarios**: In edge cases where the standard iteration loop fails, you can try to fine-tune these slope values. For example, if the text edges are slightly blurred but the background compression is sufficient, you can increase the value of fg\_slope appropriately to improve foreground quality, while slightly decreasing the value of bg\_slope to compensate for the increased file size.  
* **Reference Value**: According to public information, archive.org uses some default settings when processing books. When pursuing high compression rates, they use bg\_slope=44250 (with 3x downsampling); when pursuing higher accuracy, they use bg\_slope=43500 (without downsampling) 6. These values ​​can serve as a starting point for advanced tuning.

### **Table 3: recode\_pdf advanced parameter tuning**

| Parameter name | Default value/reference value | Effect description | Recommended use cases |
| :---- | :---- | :---- | :---- |
| fg\_slope | Ref: 45000 | Controls the JPEG2000 compression quality of the foreground layer (text). The higher the number, the higher the quality and the larger the file size. | When the text clarity is insufficient but the file size is close to the target, this value can be increased appropriately. |
| bg\_slope | Ref: 44250, 43500 | Controls the JPEG2000 compression quality of the background layer (image). The higher the number, the higher the quality and the larger the file size. | This value can be increased when the background image has too much noise or color blocks, but the overall file size is sufficient. Conversely, this value can be reduced for further compression. |

### **6.3 Performance considerations and limitations**

* **Performance Impact**: The DAR process is computationally intensive. Among them, the image rendering of pdftoppm and the OCR process of tesseract are the main performance bottlenecks, especially for documents with many pages and high resolution. Processing a large PDF file may take several minutes.  
* **Limitations**:
  * **Content Type**: This process is best suited for scan-generated, text-based documents. For native digital PDFs (vector graphics and embedded fonts), rasterizing and rebuilding them may result in a loss of quality and an increase in file size.  
  * **Complex Layout**: For pages containing a large number of charts, formulas or complex layout, the accuracy of OCR and the segmentation effect of recode\_pdf may be affected.  
  * **hOCR Dependency**: The current version of recode\_pdf is strongly dependent on hOCR files and cannot compress images alone and generate PDF 1 without a text layer.

### **6.4 Final recommendations and future work**

Final recommendations:
The automation tool blueprint detailed in this report is feasible and powerful. It is recommended that in actual development, priority should be given to implementing the core DAR process and hierarchical iterative algorithm. After the function is stable, split protocols and more complex error handling logic will be gradually added. For end users, the processing time and scope of application of the tool should be clearly communicated.  
**Future work and potential enhancements**:

* **Parallel processing**: For directory input mode, you can use Python's multiprocessing library to implement parallel processing and execute the DAR process on multiple files at the same time, thus greatly reducing the total time-consuming of batch tasks.  
* **Intelligent content analysis**: After the deconstruction stage, a simple image analysis step can be added to determine whether the page is text-dominated, image-dominated, or mixed content, and dynamically adjust parameters such as bg-downsample and slope accordingly to achieve more refined compression.  
* **Integrated advanced parameters**: Incorporate advanced parameters such as fg\_slope and bg\_slope into the automatic iterative optimization loop to create a more dimensional parameter search space to cope with more extreme compression challenges.  
* **Graphical User Interface (GUI)**: Develop a simple graphical interface for non-technical users that encapsulates the complexity of command line tools and makes them easier to use.

#### **Works Cited**

1. archive-pdf-tools · PyPI, accessed October 8, 2025, [https://pypi.org/project/archive-pdf-tools/](https://pypi.org/project/archive-pdf-tools/)
2. How to reduce the size of a OCRed pdf file using Tesseract OCR APIs. \- Google Groups, accessed October 8, 2025, [https://groups.google.com/g/tesseract-ocr/c/ennBMpr9b50](https://groups.google.com/g/tesseract-ocr/c/ennBMpr9b50)
3. Reducing PDF size by splitting the image and compressing each area differently · Issue \#912 \- GitHub, accessed October 8, 2025, [https://github.com/ocrmypdf/OCRmyPDF/issues/912](https://github.com/ocrmypdf/OCRmyPDF/issues/912)
4. Investigating OCR and Text PDFs from Digital Collections \- Bibliographic Wilderness, accessed October 8, 2025, [https://bibwild.wordpress.com/2023/07/18/investigating-ocr-and-text-pdfs-from-digital-collections/](https://bibwild.wordpress.com/2023/07/18/investigating-ocr-and-text-pdfs-from-digital-collections/)
5. Re: How to reduce the size of PDF \- Adobe Product Community, accessed October 8, 2025, [https://community.adobe.com/t5/acrobat-discussions/how-to-reduce-the-size-of-pdf/m-p/8620335](https://community.adobe.com/t5/acrobat-discussions/how-to-reduce-the-size-of-pdf/m-p/8620335)
6. pdfcomp: new tool, discussion, compression questions · Issue \#51 ..., accessed October 8, 2025, [https://github.com/internetarchive/archive-pdf-tools/issues/51](https://github.com/internetarchive/archive-pdf-tools/issues/51)
7. split \- How can I extract a page range / a part of a PDF? \- Ask Ubuntu, accessed October 8, 2025, [https://askubuntu.com/questions/221962/how-can-i-extract-a-page-range-a-part-of-a-pdf](https://askubuntu.com/questions/221962/how-can-i-extract-a-page-range-a-part-of-a-pdf)
8. qpdf or pdftk or gs???? \- Auto Multiple Choice, accessed October 8, 2025, [https://project.auto-multiple-choice.net/boards/2/topics/7780](https://project.auto-multiple-choice.net/boards/2/topics/7780)
9. Split an input into multiple output files · Issue \#30 · qpdf/qpdf \- GitHub, accessed October 8, 2025, [https://github.com/qpdf/qpdf/issues/30](https://github.com/qpdf/qpdf/issues/30)
10. Command line tools for digitisation \- The University of Melbourne, accessed October 8, 2025, [https://blogs.unimelb.edu.au/digitisation-lab/command-line-tools-for-digitisation/](https://blogs.unimelb.edu.au/digitisation-lab/command-line-tools-for-digitisation/)