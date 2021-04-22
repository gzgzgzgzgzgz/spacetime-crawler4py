import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from simhash import Simhash

#global variables

#unique urls =>expected result 1
urls_detected = set()
#TODO: longest page =>expected result 2
# first -> url second -> number 
longest_page = ['', 0]
#TODO: find 50 most common words =>expected result 3
words_count = dict()
#TODO: find number of subdomain =>expected result 4
subDomain = dict()
#simhash set
simhashes = set()

def scraper(url, resp):
    # need to check whether it is the subdomain
    if resp.status >= 200 and resp.status <= 299 and resp.status != 204 and resp.raw_response is None:
        return []
    print("Detecting URL: ", url)
    subdomain_file = open("subdomain.txt", 'a')
    links = extract_next_links(url, resp)
    # check subdomain
    for link in links:
        if is_subdomain(link):
            actual_subdomain = extract_subdomain(link)
            if actual_subdomain in subDomain:
                subDomain[actual_subdomain] = subDomain[actual_subdomain] + 1
            else:
                subDomain[actual_subdomain] = 1
                subdomain_file.write(actual_subdomain+"\n")
    subdomain_file.close()
    return links

def extract_next_links(url, resp):
    extractedLinks = set() # contains the links extracted in this round

    if resp.status >= 200 and resp.status <= 299 and resp.status != 204: # 204 -> no content
        result_file = open("result.txt", "a")
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        filtered_content = filter_label(soup)
        if len((re.sub(r'[^\w]+', ' ', filtered_content)).split(" ")) > longest_page[1]:
            longest_page_file = open("longest_page.txt", 'w')
            longest_page[0] = url
            longest_page[1] = len((re.sub(r'[^\w]+', ' ', filtered_content)).split(" "))
            longest_page_file.write(str(longest_page[0]))
            longest_page_file.write(str(longest_page[1]))
            
        wordsCount(soup)
        for link in soup.find_all('a', href=True):
            currentURL = link.get('href')
            # check relative path or absolute path
            if currentURL.startswith("http") or currentURL.startswith("https"):
                finalURL = currentURL.split('?')[0].split('#')[0]
            else:
                finalURL = urljoin(currentURL, url).split('?')[0].split('#')[0] #relative path
            finalURL = finalURL.rstrip('/')       
                
            if is_valid(finalURL):
                if simhashfinalURL not in urls_detected and simhash_filter(soup):
                    extractedLinks.add(finalURL)
                    urls_detected.add(finalURL)
                    result_file.write(finalURL+"\n")
        result_file.close()
        return extractedLinks
    else:
        return []

def distance(v1, v2):
    x = (v1 ^ v2) & ((1 << 64) - 1)
    ans = 0
    while x:
        ans += 1
        x &= x - 1
    return ans

def simhash_filter(soup):
    text = filter_label(soup)
    fingerprint = Simhash((re.sub(r'[^\w]+', ' ', text)).split(" ")).value
    for simhash_ in simhashes:
        if distance(fingerprint, simhash_) < 3:
            return False
    simhashes.add(fingerprint)
    return True


def filter_label(soup):
    ''' 
    return actual html content that is filtered by BLACKLIST
    e.g <script> <style> html label
    '''
    text = soup.find_all(text=True)
    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    return output.strip()

def is_valid(url):
    try:
        parsed = urlparse(url)
        # if parsed.scheme not in set(["http", "https"]):
        #     return False
        if not re.match(r".*(\.ics\.uci\.edu|\.cs\.uci\.edu"
                        + r"|\.informatics\.uci\.edu|\.stat\.uci\.edu)$", parsed.netloc.lower()):
            if not (re.match(r"today\.uci\.edu", parsed.netloc.lower()) and 
            re.match(r"\/department\/information_computer_sciences\/.*", parsed.path.lower())):
                return False
        if re.match(r".*\/(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|calendar|img|image|events|event"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ppsx"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)\/", parsed.path.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|ppsx"
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


def is_subdomain(url):
    '''
    return true when the input url is a subdomain of ics.uci.edu, false otherwise
    e.g. is_subdomain('https://vision.ics.uci.edu') -> True
    '''
    try:
        parsed = urlparse(url)
        if parsed.netloc.lower().startswith('www.'):
            netloc = parsed.netloc.lower()[4:]
        else:
            netloc = parsed.netloc.lower()
        if re.match(r".*\.ics\.uci\.edu$", netloc):
            return True
        else:
            return False
    except TypeError:
        print("TypeError for ", parsed)
        raise
        
def extract_subdomain(url):
    if is_subdomain(url):
        try:
            parsed = urlparse(url)
            return parsed.scheme.lower()+'://'+parsed.netloc.lower()
        except TypeError:
            print("TypeError for ", parsed)
            raise

def wordsCount(soup):
    tokenizer = RegexpTokenizer(r'\w+')
    content = tokenizer.tokenize(filter_label(soup))
    for word in content:
        word = word.lower()
        if word not in STOPWORDS:
            if word not in words_count:
                words_count[word] = 1
            else:
                words_count[word] += 1
    print(words_count)
    word_count_file = open("words_count.txt", "w")
    sum = 0
    for i,j in sorted(words_count.items(), key = lambda a: a[1]):
        if sum < 50:
            word_count_file.write(str(i) + " : " +  str(j) + '\n')
        sum += 1
    words_count.close()


STOPWORDS = [
	'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 
	'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 
	'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', 
	"couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 
	'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', 
	"hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 
	'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 
	'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', 
	"it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 
	'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 
	'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't",
	'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 
	'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 
	'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", 
	"they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 
	'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', 
	"what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 
	'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd",
	"you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', ' '
]

BLACKLIST = [
    '[document]',
    'noscript',
    'header',
    'html',
    'meta',
    'head', 
    'input',
    'script',
    'style',
]