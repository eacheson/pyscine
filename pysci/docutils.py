import pickle
import numpy as np
import xml.etree.ElementTree as ET

PDF_extension = '.pdf'
XML_extension = '.cermxml'
TXT_extension = '.txt'

### ScienceDoc CLASS ###

class ScienceDoc:
    def __init__(self, corpus_name, file_name, has_text=False, has_xml=False):
        self.corpus_name = corpus_name
        self.file_name = file_name
        self.has_text = has_text
        self.has_xml= has_xml


### GENERAL FUNCTIONS ###

def load_data(pathToPickleFile):
    """
    Read in pickled file or dir.
    File:  ground_truth_dict = load_data('ground_truth.pkl')
    Dir:   ground_truth_dict = load_data(os.path.join(output_dir, 'ground_truth.pkl'))
    :param pathToPickleFile: pickled file to read in, e.g. 'dataset.pkl'
    :return: the data from the pickled file
    """
    with open(pathToPickleFile, 'rb') as pickle_file:
        data = pickle.load(pickle_file)
    return data

def pickle_data(data, pathToPickleFile):
    """
    Pickle data to the specified file.
    Example use: pickle_data(ground_truth_dict, os.path.join(output_dir, 'ground_truth.pkl'))
    :param data: variable / data structure to pickle, e.g. myDict
    :param pathToPickleFile: file for pickling, e.g. 'dataset.pkl')
    :return:
    """
    with open(pathToPickleFile, 'wb') as pickle_file:
        pickle.dump(data, pickle_file)
    print("pickled data at " + pathToPickleFile)
    return True

def remove_extension(filename):
    if filename:
        return str(filename).rsplit(sep='.', maxsplit=1)[0]
    return np.NaN


### XML PROCESSING FUNCTIONS ###

def get_article_title(xml_root):
    for title_group in xml_root.iter('title-group'):
        for title_child in title_group:
            if title_child.tag == 'article-title':
                return title_child.text

def get_publication_year(xml_root):
    for group in xml_root.iter('pub-date'):
        for child in group:
            if child.tag == 'year':
                return child.text

def get_journal_title(xml_root):
    for journal_title_group in xml_root.iter('journal-title-group'):
        for child in journal_title_group:
            if child.tag == 'journal-title':
                return child.text

def extract_content_text(xml_root):
    """
    Returns all sections under a p node. After each identified p section, adds a
    string interpretation of a paragraph break, i.e. two line-breaks.
    :param xml_root: root of xml parse
    :return: the content as a string
    """
    xml_par_text = ''
    for par in xml_root.iter('p'):
        if par:
            xml_par_text += par.text
            xml_par_text += '\n\n'
    return xml_par_text

def get_article_authors_affiliations(xml_root):
    """
    Returns a rather a list of authors and a dict of affiliations that can be further linked.
    Authors are a list, where each list element (tuple) should consist of an author name then a reference
    number referring to which affiliation they have.
    The affiliations are then a dict, where keys are reference numbers of the affiliation (which should match
    those listed for each author) and values are whatever details were available for this affiliation, as a list
    (variable number of elements, with largest geographical entity last).
    :param xml_root: root of xml parse
    :return: a list of authors and a dict of affiliations
    """
    authors = []
    affiliations = {}
    for contrib_group in xml_root.iter('contrib-group'):
        for contrib_child in contrib_group:
            if contrib_child.tag == 'contrib':
                name = contrib_child.find('string-name').text
                refs = []
                for ref in contrib_child.findall('xref'):
                    refs.append(ref.text)
                authors.append((name, refs))
            if contrib_child.tag == 'aff':
                affiliation = []
                label = 'none'
                for aff_child in contrib_child:
                    if aff_child.tag == 'label':
                        label = aff_child.text
                    else:
                        affiliation.append(aff_child.text)
                affiliations[label] = affiliation
    return authors, affiliations

def get_affiliation_countries(xml_root):
    """
    Returns a list of 2-letter country codes that Cermine found in the affiliations. This function
    just looks at the Cermine XML and extracts these country codes when they are present.
    :param xml_root: root of xml parse
    :return: a list of country codes listed in affiliations; list may be empty
    """
    countries = []
    for contrib_group in xml_root.iter('contrib-group'):
        for contrib_child in contrib_group:
            if contrib_child.tag == 'aff':
                for aff_child in contrib_child:
                    if aff_child.tag == 'country':
                        if 'country' in aff_child.attrib:
                            country = aff_child.attrib['country']
                            countries.append(country)
    return countries
