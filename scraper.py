import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

#global variables

#unique urls
urls_detected = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    extractedLinks = set() # contains the links extracted in this round

    urls_detected.add(urldefrag(url)[0])

    if resp.status >= 200 and resp.status <= 299 and resp.status != 204: # 204 -> no content
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            currentURL = link.get('href')
            # check relative path or absolute path
            if currentLink.startswith("http") or currentLink.startswith("https"):
                finalURL = currentURL.split('?')[0].split('#')[0]
            else:
                finalURL = urljoin(currentURL, url).split('?')[0].split('#')[0] #relative path
            # other traps possible
            if "/calendar" in finalURL:
                finalURL = finalURL.split("/calendar", 1)[0]
            extractedLinks.add(finalURL)
        return extractedLinks
            
            
    else:
        return []
    


    
    




def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
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