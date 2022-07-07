from bs4 import BeautifulSoup as Soup
from oauth2client.service_account import ServiceAccountCredentials
import gspread, requests, time

def get_soup(link):
    req = requests.get(link)
    return Soup(req.text, "html.parser")

def get_root_article_link():
    soup = get_soup(f"{TWEENTRIBUNER_URL}/{CATEGORIES[0]}")

    root_article_blocks = soup.findAll("div", "article-wrapper")
    root_article_links =  [block.find("a")["href"] for block in root_article_blocks]

    return root_article_links

def scraping(root_article_links):

    index = 1
    for link in root_article_links:
        
        for category in CATEGORIES:

            result = list()

            altered_link = link.replace("/junior/", category)
            soup = get_soup(TWEENTRIBUNER_URL + altered_link)
            
            url = TWEENTRIBUNER_URL + altered_link
            title = soup.find("div", "article-headline no-printer").text.strip()
            author = soup.find("div", "article-byline").text.split(",")[0]
            lexile = soup.find("span", "lexile-active").text
            grade = soup.find("div", "nav-options").find("div", "nav-option active").text
            date = soup.find("div", "article-date no-printer").text
            img = soup.select_one("#article-page-wrapper > div.article-content > span.teaser_content > img")["src"]
            text = soup.find("span", "teaser_content").text.split("Source URL:")[0].strip()
            categories = " / ".join([atag.text for atag in soup.find("div", "article-categories").findAll("a")])
            try:
                question = soup.find("div", "critical-thinking-question").find("div", "black").text
            except:
                question = ""

            result.extend([url, title, author, lexile, grade, date, img, text, categories, question])
            write_gspread(worksheet, index, result)
            index += 1
            time.sleep(2)

def connect_gspread(file_name):
    scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = 'lxper.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)

    try:
        sheets = gc.open(file_name)
    except:
        sheets = gc.create(file_name)

    return sheets

# 여기서 왜 오류가 발생하지 않을까?  
def write_gspread(worksheet, index, result):
    worksheet.update(f"A{index}:J{index}", [result])

TWEENTRIBUNER_URL = "https://www.tweentribune.com"
CATEGORIES = ["/junior/", "/tween56/", "/tween78/", "/teen/"]
GSPREAD_FILE = "Tween Tribune Scraping"
sheets = connect_gspread(GSPREAD_FILE)    
worksheet = sheets.sheet1
root_article_links = get_root_article_link()
scraping(root_article_links)
