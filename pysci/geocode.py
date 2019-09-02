import time
import googlemaps

NO_RESULT_STRING = 'no-geocode-result'

def clean_for_geocode(orig_str):
    """
    Remove punctuation and stopwords at the end of the string only, repeatedly.
    :param orig_str: original string
    :return: clean string, ready to be geocoded
    """
    stopwords = ['in', 'the', 'upon', 'of', 'at', 'within', 'to', 'along', 'near']
    prev_len = len(orig_str)
    clean_str = orig_str
    while True:
        clean_str = clean_str.strip(" (,).")
        # remove stopwords at the end of the word
        if clean_str.split(" ")[-1] in stopwords:
            clean_str = " ".join(clean_str.split(" ")[0:-1])
        if len(clean_str) == prev_len:
            break
        prev_len = len(clean_str)
    return clean_str

def create_google_geocoder(api_key):
    #gmaps_geocoder = googlemaps.Client(key=get_api_key(path_to_key))
    gmaps_geocoder = googlemaps.Client(key=api_key)
    return gmaps_geocoder

# example function if storing key in a file with a line like:
# API key: 'YOUR-API-KEY-HERE'
def get_api_key(filepath):
    f = open(filepath, 'r')
    for line in f:
        if (line.startswith("API")):
            key = line.split("'")[1]
            return key
    return None

def geocode_google(querytext, geocoder, return_top=True):
    geocode_result = geocoder.geocode(querytext)
    if geocode_result:
        if return_top:
            return geocode_result.pop()
        else:
            return geocode_result
    return []

def geocode_with_cache_google(query_text, geocoder, cache, verbose=False):
    """
    Wrapper around geocode_google function which makes it check a cache first.
    :param query_text: the string to geocode
    :param geocoder: googlemaps.Client object to do the geocoding with
    :param cache: a dict of query_string:top_result
    """
    if query_text in cache:
        if verbose:
            print("We had a cached result.")
        return cache[query_text]
    else:
        top_result = geocode_google(query_text, geocoder)
        time.sleep(0.2)
        # add to cache
        cache[query_text] = top_result
        return top_result
