import pypdf
import Levenshtein as leven


NUMERICAL_CHARS = {str(i) for i in range(10)} | {".", "-"}


def read_pdf(filename, rm_duplicates=False):
    """
    Wraps the pypdf.PdfReader constructor with only the options I want.
    """
    if rm_duplicates:
        remove_duplicate_pages(filename)
    return pypdf.PdfReader(filename)


def pdf_writer(filename=None):
    return pypdf.PdfWriter(filename)


def remove_duplicate_pages(pdf_file):
    """
    Removes duplicate pages from a pdf file. If two or more pages in a document have identical text, then all but the
    first instance is removed.
    """
    old_doc = read_pdf(pdf_file)
    new_doc = pdf_writer()
    full_text = []
    for i, page in enumerate(old_doc.pages):
        page_text = page.extract_text()
        for prev_page in full_text:
            if leven.ratio(page_text, prev_page, score_cutoff=0.9):
                break
        else:
            new_doc.append(old_doc, pages=[i,])
            full_text.append(page_text)
    new_doc.write(pdf_file)
    return


def vprint(s, verbose=False):
    if verbose:
        print(s)


def check_numeric(string):
    """
    The built-in string methods to check for numerics don't recognize periods or hyphens, either of which may appear
    in a section number. Appendices are also problematic, and get handled separately.
    """
    if string.lower().startswith("appendix") and string.count(" ") == 1:
        return True
    return all(c in NUMERICAL_CHARS for c in string)


def letter_to_number(s):
    """
    This function takes the index from a lettered list and returns the corresponding number. The lettering is assumed
    to be in standard appendix-lettering format:
        input:  A, B, C, ... ,  Z, AA, BB, ...
        output: 1, 2, 3, ... , 26, 27, 28, ...
    """
    if any(c != s[0] for c in s):
        return -1
    return len(s) * (ord(s[0].upper()) - ord('A') + 1)


def number_to_letter(n):
    """Inverse of the letter_to_number function"""
    q, r = divmod(n-1, 26)
    return chr(ord('A') + r) * (q + 1)


def strip_nonnumeric(s, from_right=True, from_left=False):
    """
    Strips non-numeric characters from one or both sides of a string.
    """
    if from_right:
        while len(s) and not s[-1].isdigit():
            s = s[:-1]
    if from_left:
        while len(s) and not s[0].isdigit():
            s = s[1:]
    return s


if __name__ == "__main__":
    f = "C:/Users/jacio/Documents/School/Textbooks/1 Gordon Hobbs - A Formal Theory of Commonsense Psychology - Copy.pdf"
    remove_duplicate_pages(f)
