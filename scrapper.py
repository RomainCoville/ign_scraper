import pandas as pd
from bs4 import BeautifulSoup
import requests
import warnings
from tqdm import tqdm
import time

warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def scrap_data(url: str) -> pd.DataFrame:
    page = requests.get(url, verify=False)

    soup = BeautifulSoup(page.text, 'html.parser')
    res = {'title': [], 'link': []}

    articles = soup.find_all('article')
    for elt in tqdm(articles):
        try:
            res['title'].append(elt.find('h3').get_text())
            res['link'].append(str(elt.find('a', href=True)).split('"')[3])
        except Exception as e:
            continue

    df = pd.DataFrame(res)
    df.link = df.link.apply(lambda x: url + x if 'https' not in x else x)
    return df


def get_article_data(url: str) -> tuple[str, str]:
    try:
        content = requests.get(url, verify=False)
        soup_content = BeautifulSoup(content.text, 'html.parser')
    except Exception as e:
        time.sleep(5)
        try:
            content = requests.get(url, verify=False)
            soup_content = BeautifulSoup(content.text, 'html.parser')
        except Exception as e:
            author = None
            published_date = None
            return author, published_date
    try:
        author = soup_content.find('span', class_='reviewer hcard').get_text()
    except Exception as e:
        author = None
    try:
        published_date = soup_content.find('div', class_='article-publish-date').get_text().split('el')[-1].strip()
    except Exception as e:
        published_date = soup_content.find('span', class_='publish-date').get_text()

    return author, published_date
