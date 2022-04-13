import re
from datetime import timedelta
from io import BytesIO, StringIO
from typing import Any, Dict, Union

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfparser import PDFParser, PDFSyntaxError
from pdfminer.pdftypes import PDFObjRef

WORDS_PER_MIN = 200


def get_read_time(page: str) -> timedelta:
    """Get the estimated read time of a string of content."""
    word_count = sum(count_words_in_line(line) for line in page.splitlines())
    return timedelta(minutes=word_count / WORDS_PER_MIN)


def count_words_in_line(line: str):
    """Count the number of words in a line."""
    # Each entry is true if a word, false if a linebreak or something else
    is_word_list = [re.search("[a-zA-Z0-9]", word) is not None for word in line.split(" ")]
    return sum(is_word_list)


def get_pdf_info(
    pdf_byte_stream: BytesIO, use_gpt3: bool = False
) -> Dict[str, Union[str, timedelta]]:
    """Extract info from a pdf. Relies on the info being set on the pdf.

    Adapted from Yusuke Shinyamas PDFMiner documentation
    """
    # Create the document model from the file
    parser = PDFParser(pdf_byte_stream)
    try:
        document = PDFDocument(parser)
    except PDFSyntaxError:
        return {"error": "PDF Syntax Error"}
    # Try to parse the document
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    # Create a PDF resource manager object
    # that stores shared resources.
    rsrcmgr = PDFResourceManager()
    # Create a buffer for the parsed text
    retstr = StringIO()
    # Spacing parameters for parsing
    laparams = LAParams()
    codec = "utf-8"

    # Create a PDF device object
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # Create a PDF interpreter object
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)

    parsed_page = retstr.getvalue()
    info: Dict[str, str] = parse_pdf_metadata(next(iter(document.info), {}))

    return {
        "author_name": info.get("Author", ""),
        "title": info.get("Title", ""),
        "description": info.get("Subject", "") or parsed_page[:512],
        "read_time": get_read_time(parsed_page),
    }


def parse_pdf_metadata(metadata: Dict) -> Dict[str, str]:
    """Parse the metadata from a pdf document info."""

    def convert_to_string(val: Any) -> str:
        if isinstance(val, PDFObjRef):
            return val.resolve()
        try:
            if isinstance(val, bytes):
                return val.decode("utf-8")
        except UnicodeDecodeError:
            return val.decode("utf-16")
        return val

    return {key: convert_to_string(value) for key, value in metadata.items()}
