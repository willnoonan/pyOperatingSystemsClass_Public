from typing import List
import argparse
import os


"""
Author: William Noonan

    This script reads and converts PDF files to another file type (default is text).
    
    CL Usage:
        python pdf2file.py <pdf-file> [-o <output-file>] [-e <extension>]
    
    where
        optional arg output-file specifies new name of file (must include an extension).
        optional arg extension keeps name of PDF file.
"""


try:
    import pdfplumber
except ModuleNotFoundError:
    import subprocess, sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                           'pdfplumber'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_file")
    parser.add_argument("-e", dest="extension", default=".txt")
    parser.add_argument("-o", dest="output_file")
    args = parser.parse_args()

    if args.output_file:
        output_file = args.output_file
    else:
        output_file = os.path.splitext(args.pdf_file)[0] + args.extension

    with pdfplumber.open(args.pdf_file) as pdf:
        with open(output_file, "w") as fout:
            for page in pdf.pages:
                fout.write(page.extract_text())

if __name__ == "__main__":
    main()
