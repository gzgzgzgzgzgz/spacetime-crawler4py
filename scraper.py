import re
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.request import urlopen
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from simhash import Simhash
from urllib.error import URLError, HTTPError
import ssl

#global variables

#unique urls =>expected result 1
urls_detected = set()
# first -> url second -> number 
longest_page = ['', 0]
words_count = dict()
subDomain = dict()
#simhash set
simhashes = set()

def scraper(url, resp):
    # need to check whether it is the subdomain
    if resp.status < 200 or resp.status > 299 or resp.status == 204 or resp.raw_response is None:
        return []
    print("Detecting URL: ", url)
    subdomain_file = open("subdomain.txt", 'w')
    links = extract_next_links(url, resp)
    # check subdomain
    for link in links:
        if is_subdomain(link):
            actual_subdomain = extract_subdomain(link)
            if actual_subdomain in subDomain:
                subDomain[actual_subdomain] = subDomain[actual_subdomain] + 1
            else:
                subDomain[actual_subdomain] = 1
    for link, times in subDomain.items():
        subdomain_file.write(link+" "+str(times)+"\n")
    subdomain_file.close()
    return links

def extract_next_links(url, resp):
    extractedLinks = set() # contains the links extracted in this round

    if resp.status >= 200 and resp.status <= 299 and resp.status != 204: # 204 -> no content
        result_file = open("result.txt", "a")
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

        text = filter_text(soup)
        if len(text) > longest_page[1]:
            longest_page_file = open("longest_page.txt", 'w')
            longest_page[0] = url
            longest_page[1] = len(text)
            longest_page_file.write(str(longest_page[0]) + " " +  str(longest_page[1])) 
            
        wordsCount(soup)
        for link in soup.find_all('a', href=True):
            currentURL = link.get('href')
            # check relative path or absolute path
            if currentURL.startswith("http") or currentURL.startswith("https"):
                finalURL = currentURL.split('?')[0].split('#')[0]
            elif currentURL.startswith('//'):
                finalURL = 'http:'+currentURL
            elif currentURL != '' and currentURL is not None and currentURL[0] == '/':
                finalURL = urlparse(url).scheme+'://'+urlparse(url).netloc.lower()+currentURL
            else:
                if url[-1] != '/':
                    url += '/'
                finalURL = urljoin(url, currentURL).split('?')[0].split('#')[0] #relative path
            finalURL = finalURL.rstrip('/')


            try:
                # ssl._create_default_https_context = ssl._create_unverified_context
                if is_valid(finalURL) and is_valid(urlopen(finalURL).geturl()) and finalURL not in urls_detected:
                    # check similarity
                    try:
                        finalURL_content = urlopen(finalURL,timeout = 4).read()
                        finalURL_soup = BeautifulSoup(finalURL_content, "html.parser")
                    except:
                        result_file.close()
                        print("URL 404 or time out, jump to the next URL")
                        return extractedLinks
                    if simhash_filter(finalURL_soup):
                        text_len = len(re.findall(r'[a-zA-Z0-9][-@\/:a-zA-Z0-9]+[a-zA-Z0-9]', finalURL_soup.get_text()))
                        num_len = len(re.findall(r'[0-9]+', finalURL_soup.get_text()))
                        if num_len<text_len:
                            extractedLinks.add(finalURL)
                            urls_detected.add(finalURL)
                            result_file.write(finalURL+"\n")
            except:
                with open('error.txt', 'a') as outfile:
                    outfile.write('except: '+finalURL)
                
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
    fingerprint = Simhash(soup.get_text(), reg = r"[a-zA-Z0-9][-@\/:a-zA-Z0-9]+[a-zA-Z0-9]").value
    for simhash_ in simhashes:
        if distance(fingerprint, simhash_) < 3:
            return False
    simhashes.add(fingerprint)
    return True

# return a list of text after filtered
def filter_text(soup):
    return re.findall(r'[a-zA-Z0-9][-@\/:a-zA-Z0-9]+[a-zA-Z0-9]', soup.get_text())


def is_valid(url):
    try:
        parsed = urlparse(url)
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
            + r"|thmx|mso|arff|rtf|jar|csv|odc"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)\/", parsed.path.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico|ppsx"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|odc"
            + r"|epub|dll|cnf|tgz|sha1|nb|Z|in|sas|"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|java|apk|war|img|sql)$", parsed.path.lower())
    

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
            return parsed.netloc.lower()
        except TypeError:
            print("TypeError for ", parsed)
            raise

def wordsCount(soup):
    content = filter_text(soup)
    for word in content:
        word = word.lower()
        if word not in STOPWORDS and not word.isnumeric():
            if word not in words_count:
                words_count[word] = 1
            else:
                words_count[word] += 1
    word_count_file = open("words_count.txt", "w")
    sum = 0
    for i,j in sorted(words_count.items(), key = lambda a: a[1], reverse=True):
        if sum < 100:
            word_count_file.write(str(i) + " : " +  str(j) + '\n')
        sum += 1
    word_count_file.close()


STOPWORDS = [
	'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'will',
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
