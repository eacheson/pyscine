import re
from nltk.tokenize.moses import MosesDetokenizer

detokenizer = MosesDetokenizer()

### STRINGS AND REGULAR EXPRESSIONS ###
NO_METHODS_STRING = "no-methods-found"
NO_LOCATIONS_STRING = "no-locations-found"
NO_TITLE_STRING = "no-title"
NO_XML_STRING = "no-xml"
RE_INITIAL_CAPITAL = r'[0-9.]*[ \t]{0,2}[A-Z]'
RE_ORCHARDS_METHODS_TEXT = r'[0-9.]*[ \t]{0,2}(the )?(material|method|study[ \t]{0,2}(area|site|region))'
RE_BIOMED_METHODS_TEXT = r'[0-9.]*[ \t]{0,2}(the )?(material|method|(experimental procedure)|sample|tumor|tumour|patient|specimen|subject|population|human)'
RE_ORCHARDS_METHODS_HEADINGS = r'[0-9.]*[ \t]{0,2}(the )?(material|method|location|region|study[ \t]{0,2}(area|site|region)|(\w+[ \t]{0,2}){0,2}(orchard|location))'
RE_BIOMED_METHODS_HEADINGS = r'[0-9.]*[ \t]{0,2}(the )?(material|method|(experimental procedure)|(\w+[ \t]{0,2}){0,2}(tumor|tumour|patient|sample|specimen|subject|population|human))'


### FUNCTIONS ###

def multireplace(string, replacements={"u¨ ":"ü","a¨ ":"ä","o¨ ":"ö","o ¨":"ö","o´ ":"ó","aˆ ": "â","oˆ ": "ô","u¨":"ü","a¨":"ä","o¨":"ö","a´":"á","e´":"é","o´":"ó","aˆ": "â","oˆ": "ô","i´":"í","ı´":"í", "a`":"à","o`":"ò","i`":"ì","u`":"ù","e`":"è","ﬂ":"fl","a˜":"ã","¨ı":"i","ó n ":"ón ","U´ ":"Ú"}):
    """
    Given a string and a replacement map, it returns the replaced string.
    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :rtype: str
    """
    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, replacements)))
    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)

def tuple_list_to_string(tuple_list):
    """
    Given a list of (word, type) tuples, return a reconstituted (detokenized) string
    representation of the words. This function uses NLTK's MosesDetokenizer, then does
    a brief tidy-up.
    NOTE: assumed "detokenizer" has already been created outside the function.
    """
    token_list = [item[0] for item in tuple_list]
    moses_string = detokenizer.detokenize(token_list, return_str=True)
    # add tidying up stuff here as needed/discovered
    moses_string_clean = moses_string.replace("( ", "(")
    return moses_string_clean

def extract_methods_text(article_content, par_range=4, max_words_in_heading=8, re_to_match=RE_BIOMED_METHODS_TEXT, verbose=False):
    """
    Methods section detection function for raw-text content, which returns both the headings
    found and the text content identified. Because we don't have much structure in the
    raw-text article, we don't keep track of which text is with which section heading.
    :param article_content: the full raw text contents of the article
    :param par_range: how many paragraphs to look for placenames in after the heading
    :param max_words_in_heading: upper limit on number of words in a heading (inclusive)
    :param verbose: whether to print debug-style output
    :return: a two-item tuple: methods_titles (list), text_contents (string)
    """
    methods_titles = []
    # split on two or more line-break chars for 'paragraphs'
    pars = re.split('[\n]{2,}', article_content)
    if verbose:
        print("article has %s 'paragraphs'" % len(pars))
    indexes = []
    for i, par in enumerate(pars):
        # fix split words (but will also erroneously de-hyphen hyphenated words broken up by a line-break)
        clean_par = re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', par)
        candidate_title = clean_par.split('\n')[0]
        # check for an initial capital letter and put a somewhat arbitrary (but customizable) length restriction
        if (re.match(RE_INITIAL_CAPITAL, candidate_title) and len(candidate_title.split(' ')) <= max_words_in_heading):
        # now finally match our more complex RE
            if re.match(re_to_match, candidate_title.lower()):
                methods_titles.append(candidate_title)
                indexes.append(i)
                if verbose:
                    print("Found section match: " + candidate_title)
    # found no methods sections - exit now
    if not indexes:
        return ([], '')
    # make a unique list of indexes
    extended = []
    for i in indexes:
        extended.extend(list(range(i, i + par_range)))
    paragraph_indexes = list(set(extended))
    paragraph_indexes.sort()
    text_contents = ''
    for i in paragraph_indexes:
        try:
            par = pars[i]
            par_temp = re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', par)  # this fixes split words
            par_temp = par_temp.replace('\n', ' ') # ignore single line breaks due to formatting
            text_contents += par_temp
            text_contents += '\n\n'
        except IndexError:
            # this happens if we found a dodgy heading near the end of the document
            continue
    return (methods_titles, text_contents)

def extract_methods_xml(xml_root, re_to_match=RE_BIOMED_METHODS_HEADINGS, par_range=3, verbose=False):
    """
    Methods section detection function for XML content, which returns both the headings
    found and the text content identified. Rather complicated code because no easy way
    to access sibling nodes.
    :param xml_root: root of the XML doc produced by Cermine
    :param par_range: how many paragraphs to look for placenames in after the heading
    :param verbose: whether to print debug-style output
    :return: a list of (section_title, text_contents) tuples
    """
    methods = [] # store the tree node too: (section_title, text_contents)
    # iterate over parent
    for sec in xml_root.iter('sec'):
        foundMethods = False
        visited_pars = 0
        section_title = ''
        text_contents = ''
        for child in sec:
            if not foundMethods:
                if child.tag == 'title':
                    if re.match(re_to_match, child.text.lower()):
                        foundMethods = True
                        section_title = child.text
                        if verbose:
                            print("Found methods section match: %s" %child.text)
            elif foundMethods:
                if visited_pars >= par_range:
                    if verbose:
                        print("max paragraphs reached: breaking")
                    break
                # we found a matching methods title: print/store the paragraphs in this section
                if child.tag == 'p':
                    text_contents += child.text
                    visited_pars += 1
                    # to get the 'rest' of the text of a 'p', we need to get the 'tail' of its child nodes :/
                    for xref in child:
                        # all child nodes of p should be xref...
                        text_contents += ' '
                        text_contents += xref.tail
                    # end of paragraph
                    text_contents += '\n\n'
        if foundMethods:
            methods.append((section_title, text_contents))
    return methods

# function mainly useful in testing heading detection
def detect_methods_text(article_content, max_words_in_heading=8, verbose=False):
    """
    Tries to find all section headings that are likely to contain site/sample info (and thus the locations we want).
    Returns headings but not contents.
    :param article_content: a string with the entire article text content
    :param verbose: whether to print output
    :return: list of string, where each string is (supposedly) a relevant section heading
    """
    methods = []
    # split on two or more line-break chars (== 'paragraphs')
    pars = re.split('[\n]{2,}', article_content)
    if verbose:
        print("article length: %s" % len(article_content))
        print("article has %s 'paragraphs'" % len(pars))
    for par in pars:
        # fix split words (but may also erroneously de-hyphen hyphenated words broken up by a line-break)
        clean_par = re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', par)
        candidate_title = clean_par.split('\n')[0]
        if verbose:
            print("candidate title: %s" %candidate_title)
        # check for an initial capital letter and put a somewhat arbitrary length restriction
        if (re.match(RE_INITIAL_CAPITAL, candidate_title) and len(candidate_title.split(' ')) <= max_words_in_heading):
        # now finally match our more complex RE
            if re.match(RE_BIOMED_METHODS_TEXT, candidate_title.lower()):
                methods.append(candidate_title)
                if verbose:
                    print("Found section match: " + candidate_title)
    return methods

# function mainly useful in testing heading detection
def detect_methods_xml(xml_root):
    """
    Tries to find all section headings that are likely to contain site/sample info (and thus the locations we want).
    Returns headings but not contents.
    :param xml_root: root of xml parse
    :return: list of string, where each string is a relevant section heading
    """
    methods = []
    for title in xml_root.iter('title'):
        if re.match(RE_BIOMED_METHODS_HEADINGS, title.text.lower()):
            methods.append(title.text)
    return methods

def extract_chunks_from_sentence(tagged_sentence, include_cardinal=True, include_other_spatial=True, include_types=True):
    """
    Custom NER chunker, basically grabbing consecutive sequences of tagged terms from
    a list in a format returned by NLTK's Stanford NER wrapper. We also concatenate
    commas, parentheses, and two-letter capital abbreviations (usually states) with an
    already-found chunk.
    """
    chunk_tokens = []  # for the (str, type) tuples
    tokens = []
    concatenate = False
    previous_token = ('', 'O')
    cardinal_direction_tokens = ['east', 'west', 'south', 'north', 'eastern',
                               'western', 'southern', 'northern', 'central',
                               'northeast', 'northwest', 'southeast', 'southwest',
                               'northeastern', 'northwestern', 'southeastern', 'southwestern']
    spatial_language_tokens = ['along', 'near', 'at']
    feature_type_tokens = ['region', 'regions', 'county', 'counties', 'park', 'parks',
                           'coast', 'coasts', 'town', 'city', 'state', 'states', 'river', 'rivers']
    for token in tagged_sentence:
        word = token[0]
        tag = token[1]
        # start with a loc, org, or person (we include person bc of NER errors)
        if tag == 'LOCATION' or tag == 'ORGANIZATION' or tag == 'PERSON':
            if concatenate:
                tokens.append(token)
            else:
                # new chunk: but include a previous "("
                if previous_token[0] == '(':
                    tokens.append(previous_token)
                # also keep stuff like 'north', 'south' before a relevant NER token
                if include_cardinal and previous_token[0] in cardinal_direction_tokens:
                    tokens.append(previous_token)
                tokens.append(token)
                concatenate = True
        # handle commas and other punctuation we want to keep when already in a chunk
        elif concatenate and re.match(r'[,()]|\'s', word):
            tokens.append(token)
        # handle 2-letter abbreviations with a RE (usually states)
        elif concatenate and re.match(r'\b[A-Z][A-Z]\b', word):
            tokens.append(token)
        # handle some prepositions we want to keep, some occur within placenames
        elif concatenate and re.match(r'\bin\b|\bthe\b|\bupon\b|\bof\b', word.lower()):
            tokens.append(token)
        # keep cardinal direction tokens
        elif concatenate and include_cardinal and word.lower() in cardinal_direction_tokens:
            tokens.append(token)
        # keep other spatial language tokens
        elif concatenate and include_other_spatial and word.lower() in spatial_language_tokens:
            tokens.append(token)
        # keep feature type tokens
        elif concatenate and include_types and word.lower() in feature_type_tokens:
            tokens.append(token)
        # keep 'et' because this is part of 'et al.' and we should reject these chunks down the road
        elif concatenate and re.match(r'^et$', word):
            tokens.append(token)
        else:
            # end of chunk!
            if tokens:
                chunk_tokens.append(tokens.copy())
            # re-set things
            concatenate = False
            tokens.clear()
        previous_token = token
    # this is to catch a chunk which includes the very last token in a sentence (e.g. titles)
    if concatenate:
        chunk_tokens.append(tokens.copy())
    #print("FINAL chunk_tokens: %s" %chunk_tokens)
    return chunk_tokens

def filter_chunk_candidates(sentence_tokens, chunk_list, verbose=False):
    """
    Takes as arguments the original sentence as tokens, and a list of chunks
    found by our custom location candidate chunker, and tries to filter out
    chunks like company locations, erroneously tagged references (et al),
    author initials, and so on.
    """
    chunks_filtered = []
    if len(sentence_tokens) <= 3:
        if verbose:
            print("sentence was too short!")
        return chunks_filtered
    if not chunk_list:
        if verbose:
            print("no chunks to filter!")
        return chunks_filtered
    # add more keep words as needed
    keep_words = set(['hospital', 'hospitals', 'hopital', 'hôpital', 'clinic', 'clinics', 'clinique',
                      'university', 'universities', 'universite', 'universität',
                      'centre', 'centres', 'centro', 'center', 'centers',
                      'college', 'colleges',
                      'department', 'departments', 'departamento', 'departement',
                      'institution', 'institutions', 'institute', 'institutes', 'institut', 'instituto'])
    discard_words = set(['gmbh', 'inc', 'inc.'])
    for chunk in chunk_list:
        # filter references (this works well enough, chunking step always keeps 'et' tokens)
        if chunk[-1][0] == 'et':
            if verbose:
                print("chunk was a reference: discard")
        elif re.fullmatch(r'\b[A-Z][.]([A-Z][.]?){1,2}', chunk[0][0]):
            # reject first word initials-pattern chunks
            if verbose:
                print("chunk was an initial: discard")
        else:
            tags = [item[1] for item in chunk]
            words = [item[0] for item in chunk]
            words_lower = [item[0].lower() for item in chunk]
            words_lower_set = set(words_lower)
            # reject any chunk with one of our discard words (signaling companies)
            if discard_words.intersection(words_lower_set):
                if verbose:
                    print("chunk had a discard word: discard")
            # keep any chunk with one of our keep words, no matter what (except cases above)
            elif keep_words.intersection(words_lower_set):
                if verbose:
                    print("chunk had a keyword: keep")
                chunks_filtered.append(chunk.copy())
            # rest of chunks must have at least one location and we try to block companies
            elif 'LOCATION' in tags:
                if ')' in words_lower_set:
                    if not '(' in words_lower_set:
                        # discard
                        if verbose:
                            print("no opening parenthesis: discard")
                    elif 'ORGANIZATION' in tags:
                        # TODO: check that it's actually inside the parentheses
                        if verbose:
                            print("ORG with both parentheses: discard")
                    else:
                        # no ORG: could do further triage but we just keep everything
                        if verbose:
                            print("both parentheses but no ORG: keep")
                        chunks_filtered.append(chunk.copy())
                else:
                    if '(' in words_lower_set:
                        # no closing but an opening parenthesis
                        if tags.index('LOCATION') > words_lower.index('('):
                            if verbose:
                                print("LOC right of opening parenthesis: discard")
                        else:
                            if verbose:
                                print("LOC left of opening parenthesis: keep")
                            chunks_filtered.append(chunk.copy())
                    else:
                        # filter the declaration of helsinki / helsinki declaration cases, could add more cases like this
                        if 'helsinki' in words_lower_set:
                            index_hel = sentence_tokens.index(('Helsinki'))
                            context_tokens = [word.lower() for word in sentence_tokens[index_hel-2:index_hel+2]]
                            if 'declaration' in context_tokens:
                                if verbose:
                                    print("Declaration alongside Helsinki: discard")
                            else:
                                if verbose:
                                    print("Helsinki but no declaration: keep")
                                chunks_filtered.append(chunk.copy())
                        else:
                            if verbose:
                                print("LOC final else: keep")
                            chunks_filtered.append(chunk.copy())
            else:
                # no location, don't keep
                if verbose:
                    print("final else: discard")
    return chunks_filtered
