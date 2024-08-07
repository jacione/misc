import re
from pathlib import Path

import src.utils as ut


class Entry:
    """
    Representation of a single entry in a table of contents.
    """
    def __init__(self, section, title, page):
        self.title = title
        self.page = int(page)

        if section.lower().startswith('appendix '):
            self.appendix = True
            section = section[9:]  # Strip the 'Appendix' off of the section string
            section = section.split(".")
            # Many appendices are lettered rather than numbered.
            if ut.check_numeric(section[0]):
                pass
            for i, s in enumerate(section):
                if ut.check_numeric(s):
                    section[i] = int(s)
                else:
                    section[i] = ut.letter_to_number(s)
        else:
            self.appendix = False
            section = ut.strip_nonnumeric(section, True, True)
            section = [int(x) for x in section.split(".")]

        while len(section) < 3:
            section.append(0)
        self.chapter = section[0]
        self.section = section[1]
        self.subsection = section[2]

    def __str__(self):
        if self.appendix:
            # TODO: Handle appendices.
            return f"[UNHANDLED APPENDIX]"
        elif self.subsection:
            return f"{self.chapter}.{self.section}.{self.subsection} - {self.title} (page {self.page})"
        elif self.section:
            return f"{self.chapter}.{self.section} - {self.title} (page {self.page})"
        else:
            return f"Ch. {self.chapter} - {self.title} (page {self.page})"


class Appendix(Entry):
    def __init__(self):
        pass


def split_line(line):
    """
    Split the section and page numbers off of a line from a table of contents. Appendices are treated uniquely
    """
    section, _, title = line.partition(" ")
    if section.lower() == "appendix":
        section, _, title = title.partition(" ")
        section = "Appendix " + section
    title, _, page = title.rpartition(" ")
    return section, title, page


def clean_buffer(buffer):
    """
    Remove trailing non-numerical characters from the buffer.
    """
    buffer = f"{buffer[0]} {buffer[1]} {buffer[2]}"
    return split_line(ut.strip_nonnumeric(buffer))


def offset_first_page(document, contents):
    for i, page in enumerate(document.pages):
        text = " ".join(page.extract_text().splitlines()[:3])

        if contents[0].title in text:
            for entry in contents:
                entry.page += i - 1
            return contents


def identify_toc(document, verbose=False):
    """
    Takes in a pypdf.PdfReader object and scans the text to find the table of contents.
    :param document:
    :return:
    """
    print("Scanning for table of contents...")
    toc_text = []
    toc_found = False
    for i, page in enumerate(document.pages):
        # List of all lines of text on this page
        all_lines = page.extract_text().splitlines()

        # Sublist of all lines that end with a number
        cond_lines = [line for line in all_lines if bool(re.match(r"^.*\D\d", line))]

        # If more than 75% of the lines end with a number, then it's probably a TOC page
        if len(cond_lines) > 0.75 * len(all_lines):
            ut.vprint(f"ToC on page {i}!", verbose)
            if not toc_found and len(all_lines) < 10:
                # If the FIRST page that matches the pattern has fewer than 10 lines of text, it's probably just a
                # weird frontmatter page, and we should move on. (if it's not the first match, then it could be the
                # last few lines of the TOC)
                continue
            toc_text += all_lines
            toc_found = True
        # If the pattern no longer matches, then the TOC has ended. No need to scan the entire document, especially
        # since the pattern could also match with an index, references (depending on how they're formatted), and large
        # block equations (particularly matrix equations, where the subscript is
        elif toc_found:
            break
    else:
        print("No table of contents found!")

    return toc_text


def parse_toc(document, toc_text, verbose=False):
    """
    Goes through each line of the table of contents and extracts the section, title, and page of each entry.
    """
    print("Parsing table of contents...")
    ut.vprint(toc_text, verbose)
    contents = []
    buffer = []
    for i, line in enumerate(toc_text):
        section, title, page = split_line(line)
        match bool(len(buffer)), ut.check_numeric(section), ut.check_numeric(page):
            # Simplest case
            case [False, True, True]:
                # The line starts with a section number and ends with a page number.
                contents.append(Entry(section, title, page))

            # Special cases
            case [False, True, False]:
                # The current line begins a multiline entry
                buffer = section, title, page
            case [True, False, False]:
                # The current line continues a multiline entry
                buffer = buffer[0], f"{buffer[1]} {buffer[2]} {section} {title}", page
            case [True, False, True]:
                # The current line terminates a multiline entry
                contents.append(Entry(buffer[0], f"{buffer[1]} {buffer[2]} {section} {title}", page))
                buffer = ()
            case [True, True, True]:
                # This is a backtracking case, in which the beginning of a new entry reveals that the buffer already
                # contains a complete entry. An example of this that I've seen is where the header of a page gets
                # tacked directly onto the end of the last line of body text, as in these two lines:
                #     '5.2.2 Displacement Measurement Devices 87vi Contents'
                #     '5.3 Tensile Stress –Strain Curves 88'
                # The first line would have been added to the buffer, but the second line contains a section number,
                # indicating that it is the beginning of a new entry. The response is to call clean_buffer(), which
                # hacks characters off the end of the buffer string until it hits a number.
                contents.append(Entry(*clean_buffer(buffer)))
                contents.append(Entry(section, title, page))
                buffer = ()
            case [True, True, False]:
                # Same as [True, True, True], except that the current line begins a multiline entry.
                contents.append(Entry(*clean_buffer(buffer)))
                buffer = section, title, page

            # In all other cases, there is nothing to add to the ToC. Examples of these cases are:
            # [False, False, False]:
            #     text = "Published by The Publishers Ltd."
            # [False, False, True]:
            #     text = "Homework problems 48"
            # The latter case should maybe be included in the ToC, but it would be really hard to determine where it
            # gets nested among the other entries. Homework problems would be under chapter headings in some books, but
            # section headings in others, and an index shouldn't be in either. I don't have the time to put into
            # covering every possible case.

    return offset_first_page(document, contents)


def add_bookmarks_to_pdf(document, contents, save_as, verbose=False):
    print("Adding bookmarks to PDF...")
    chapter_level = [
        entry for entry in contents
        if not any([entry.section, entry.subsection, entry.appendix])
    ]
    section_level = [
        [
            entry for entry in contents
            if all([entry.chapter == chapter.chapter, entry.section, not any([entry.subsection, entry.appendix])])
        ]
        for chapter in chapter_level
    ]
    subsection_level = [
        [
            [
                entry for entry in contents
                if all([entry.chapter == chapter.chapter, entry.section == section.section, entry.subsection, not entry.appendix])
            ]
            for section in section_level[i]
            if section.chapter == chapter.chapter
        ]
        for i, chapter in enumerate(chapter_level)
    ]

    writer = ut.pdf_writer()
    writer.append(document, import_outline=False)
    try:
        for i, chapter in enumerate(chapter_level):
            ut.vprint(chapter, verbose)
            chapter_mark = writer.add_outline_item(str(chapter), chapter.page)
            for j, section in enumerate(section_level[i]):
                ut.vprint(section, verbose)
                section_mark = writer.add_outline_item(str(section), section.page, chapter_mark)
                for subsection in subsection_level[i][j]:
                    ut.vprint(subsection, verbose)
                    writer.add_outline_item(str(subsection), subsection.page, section_mark)
        writer.write(save_as)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        writer.close()


def write_bookmarks(filename, verbose=False):
    document = ut.read_pdf(filename)
    toc_text = identify_toc(document, verbose)
    table_of_contents = parse_toc(document, toc_text, verbose)
    add_bookmarks_to_pdf(document, table_of_contents, filename, verbose)


if __name__ == "__main__":
    wd = Path("C:/Users/jacio/Documents/School/Textbooks/")
    p1 = wd / "Gordon Hobbs - A Formal Theory of Commonsense Psychology.pdf"
    p2 = wd / "Clyne Campbell - Testing of the Plastic Deformation of Metals.pdf"
    p3 = wd / "Asaro - Mechanics of Solids and Materials.pdf"
    write_bookmarks(p2, verbose=True)
