# Python 3 version of pdf conversion
import sys
import logging
import six
import os
import pdfminer
import pdfminer.settings
pdfminer.settings.STRICT = False
from pdfminer.image import ImageWriter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
from pdfminer.psparser import PSSyntaxError
import pdfminer.high_level

def convert_pdf_to_text(pdf_filepath, txt_filepath, verbose=False):
    """
    Essentially a wrapper function around extract_text which catches some errors and keep
    track ot them.
    :param pdf_filepath: path to a single pdf file
    :param txt_filepath: path for the output txt file
    :param verbose: print info for each file or not.
    :return:
    """
    no_error = False
    try:
        outFile = extract_text(files=[pdf_filepath], outfile=txt_filepath)
        if verbose:
            print("Succesfully read file at " + pdf_filepath)
            print("Succesfully output string contents to file at " + txt_filepath)
        outFile.close()
        no_error = True
    except TypeError as te:
        print("TypeError on file " + os.path.basename(pdf_filepath))
        if verbose:
            print(te)
    except PDFTextExtractionNotAllowed as pdfe:
        print("PDFTextExtractionNotAllowed on file " + os.path.basename(pdf_filepath))
        if verbose:
            print(pdfe)
    except IndexError as ie:
        print("IndexError on file " + os.path.basename(pdf_filepath))
        if verbose:
            print(ie)
    except PSSyntaxError as psse:
        print("PSSyntaxError on file " + os.path.basename(pdf_filepath))
        if verbose:
            print(psse)
    return no_error

def extract_text(files=[], outfile='-',
                 _py2_no_more_posargs=None,  # Bloody Python2 needs a shim
                 no_laparams=False, all_texts=None, detect_vertical=None,  # LAParams
                 word_margin=None, char_margin=None, line_margin=None, boxes_flow=None,  # LAParams
                 output_type='text', codec='utf-8', strip_control=False,
                 maxpages=0, page_numbers=None, password="", scale=1.0, rotation=0,
                 layoutmode='normal', output_dir=None, debug=False,
                 disable_caching=False, **other):
    """
    Converts PDF text content (though not images containing text) to plain text, html, xml or "tags".
    Function is from the script pdf2txt.py from pdfminer itself.
    """
    if _py2_no_more_posargs is not None:
        raise ValueError("Too many positional arguments passed.")
    if not files:
        raise ValueError("Must provide files to work upon!")

    # If any LAParams group arguments were passed, create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = pdfminer.layout.LAParams()
        for param in ("all_texts", "detect_vertical", "word_margin", "char_margin", "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None

    # NOTE: eacheson modified this to suppress (most) console-style output
    logging.getLogger().setLevel(logging.ERROR)

    imagewriter = None
    if output_dir:
        imagewriter = ImageWriter(output_dir)

    if output_type == "text" and outfile != "-":
        for override, alttype in ((".htm", "html"),
                                  (".html", "html"),
                                  (".xml", "xml"),
                                  (".tag", "tag")):
            if outfile.endswith(override):
                output_type = alttype

    if outfile == "-":
        outfp = sys.stdout
        if outfp.encoding is not None:
            codec = 'utf-8'
    else:
        outfp = open(outfile, "wb")

    for fname in files:
        with open(fname, "rb") as fp:
            pdfminer.high_level.extract_text_to_fp(fp, **locals())
    return outfp
