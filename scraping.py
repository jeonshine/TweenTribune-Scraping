from bs4 import BeautifulSoup as Soup
from oauth2client.service_account import ServiceAccountCredentials
import gspread, requests, time

def get_soup(link):
    req = requests.get(link)
    return Soup(req.text, "html.parser")

def root_article_links():
    # side nav article의 root => CATEGORIES[1] (tween56) 
    soup = get_soup(f"{TWEENTRIBUNER_URL}/{CATEGORIES[1]}")

    article_blocks = soup.findAll("div", "article-wrapper")
    top_nav_article_links =  [block.find("a")["href"] for block in article_blocks]

    for LEXILE in LEXILE_RANGES:
        soup = get_soup(f"{TWEENTRIBUNER_URL}/level/{LEXILE}")
        article_blocks = soup.findAll("div", "article-wrapper")
        side_nav_article_links =  [block.find("a")["href"] for block in article_blocks if block.find("a")["href"] not in top_nav_article_links]
        top_nav_article_links += side_nav_article_links
        
    soup = get_soup(f"{TWEENTRIBUNER_URL}/topic/technology/{CATEGORIES[1]}")
    article_blocks = soup.findAll("div", "article-wrapper")
    tech_nav_article_links = [block.find("a")["href"] for block in article_blocks if block.find("a")["href"] not in top_nav_article_links]
    top_nav_article_links += tech_nav_article_links

    return top_nav_article_links

def scraping(root_article_links):

    index = 1
    for link in root_article_links:
        
        for category in CATEGORIES:

            result = list()

            altered_link = link.replace("/tween56/", category)
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

def write_gspread(worksheet, index, result):
    worksheet.update(f"A{index}:J{index}", [result])

TWEENTRIBUNER_URL = "https://www.tweentribune.com"
CATEGORIES = ["/junior/", "/tween56/", "/tween78/", "/teen/"]
LEXILE_RANGES = ["500/590/", "600/690/", "700/790/", "800/890/", "900/990", "1000/1090/", "1100/1190/", "1200/1290/", "1300/1600"]
GSPREAD_FILE = "Tween Tribune Scraping"
sheets = connect_gspread(GSPREAD_FILE)    
worksheet = sheets.sheet1

article_links = root_article_links()
scraping(article_links)
