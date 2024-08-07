"""
Converts a zip file containing *ONLY* PDF files and merges them into a single PDF. The files are merged in alphabetical
order. Thus, one way to ensure the correct order is to prepend index numbers to the filenames within the zip.

NOTE TO SELF:
    To compile a new version, run `pyinstaller merge_pdfs.py --clean --onefile` from the terminal within pycharm
"""
import sys
from pathlib import Path

import zipfile
import roman

import src.utils as ut
import src.add_bookmarks_to_pdf as bkmk


def zip_to_pdf(*files):
    """
    Takes in any number of zip files containing PDF files and outputs a single
    :param files:
    :return:
    """
    print("Compiling PDFs...")
    # Define the input zip file and output PDF file
    old_files = [Path(file) for file in files]
    new_file = old_files[0].with_suffix('.pdf').as_posix()

    # Create a PDF merger object
    pdf_merger = ut.pdf_writer()
    try:
        # Extract PDFs from the zip file and add them to the PDF merger
        for old_file in sorted(old_files):
            with zipfile.ZipFile(old_file.as_posix(), "r") as zip_ref:
                for doc in sorted(zip_ref.namelist()):
                    if doc.lower().endswith(".pdf"):
                        # Open the PDF file within the zip archive
                        with zip_ref.open(doc) as pdf_file:
                            # Add the PDF to the merger
                            pdf_merger.append(pdf_file)

        # Write the combined PDF to the output file
        pdf_merger.write(new_file)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        pdf_merger.close()
    return new_file


if __name__ == "__main__":
    f = zip_to_pdf(*sys.argv[1:])
    ut.remove_duplicate_pages(f)
    bkmk.write_bookmarks(f)
    print("Done!")
