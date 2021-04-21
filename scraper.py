import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

#global variables

#unique urls =>expected result 1
urls_detected = set()
#TODO: longest page =>expected result 2
#TODO: find 50 most common words =>expected result 3
#TODO: find number of subdomain =>expected result 4

def scraper(url, resp):
    # need to check whether it is the subdomain
    if resp.status >= 200 and resp.status <= 299 and resp.status != 204 and resp.raw_response is None:
        return []
    if not is_valid(url): return []

    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    extractedLinks = set() # contains the links extracted in this round

    urls_detected.add(urldefrag(url)[0])

    if resp.status >= 200 and resp.status <= 299 and resp.status != 204: # 204 -> no content
        result_file = open("result.txt", "w")
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            currentURL = link.get('href')
            # check relative path or absolute path
            if currentLink.startswith("http") or currentLink.startswith("https"):
                finalURL = currentURL.split('?')[0].split('#')[0]
            else:
                finalURL = urljoin(currentURL, url).split('?')[0].split('#')[0] #relative path
            # TODO: Might have other things to check => could be checked in is_valid function
            
            # TODO: other traps possible
            if "/calendar" in finalURL:
                finalURL = finalURL.split("/calendar", 1)[0]
            extractedLinks.add(finalURL)
            result_file.write(finalURL)
        result_file.close()
        return extractedLinks
    else:
        return []
    

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(r".*(\.ics\.uci\.edu|\.cs\.uci\.edu"
                        + r"|\.informatics\.uci\.edu|\.stat\.uci\.edu)$", parsed.netloc.lower()):
            if not (re.match(r"today\.uci\.edu", parsed.netloc.lower()) and 
            re.match(r"\/department\/information_computer_sciences\/.*", parsed.path.lower())):
                return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise