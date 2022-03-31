import re
import time

import bs4
import demjson
import requests
from bs4 import BeautifulSoup

from src.config import CITY, SLEEP_TIME
from src.database import crud, database, models, schemas
from src.logs import LOGGER

models.Base.metadata.create_all(bind=database.engine)


class House:
    """house"""

    def __init__(self, city: str = CITY):
        """init

        Args:
            city (str, optional): which city to scrapy. Defaults to CITY.
        """
        self.base_url = f"http://{city}.lianjia.com"

    def getData(self, max_page: int = 100):
        """get house data

        Args:
            max_page (int, optional): max page to scrapy. Defaults to 100.
        """
        self.db = database.Session()
        self.session = self.initSession()
        for page in range(1, max_page + 1):
            self.getUrlsByPage(page)
            time.sleep(SLEEP_TIME)
        self.db.close()

    def initSession(self):
        """init requests session"""
        session = requests.session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.55"
        }
        session.headers.update(headers)
        session.get(self.base_url)
        return session

    def getUrlsByPage(self, page: int):
        """get house urls by page

        Args:
            page (int): page number
        """
        url = self.base_url + f"/ershoufang/pg{page}"
        req = self.session.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        divs = soup("div", {"class": "info clear"})
        urls = [div.find("a")["href"] for div in divs]
        LOGGER.info(f"Successfully get {len(urls)} urls by page {page}")
        for url in urls:
            try:
                self.getHouseByUrl(url)
            except Exception as e:
                LOGGER.error(f"Failed to get house by url {url}: {e}")
            time.sleep(SLEEP_TIME)

    def getContentByTags(self, tags: bs4.element.ResultSet):
        """get house content data by tags

        Args:
            tags (bs4.element.ResultSet): result set

        Returns:
            dict: house content data
        """
        content = {}
        for tag in tags:
            stripped_strings = [s for s in tag.stripped_strings]
            key = stripped_strings[0]
            value = ",".join(stripped_strings[1:])
            content[key] = value
        return content

    def getHouseByUrl(self, url: str):
        """get house datas by url

        Args:
            url (str): house url
        """
        req = self.session.get(url)
        html = req.text
        sell_detail_str = re.findall("init\(([\s\S]*?)\);", html)[0]
        sell_detail = demjson.decode(
            re.sub("\$\.getQuery\(.*\)", "''", sell_detail_str)
        )

        soup = BeautifulSoup(req.text, "html.parser")
        contents = soup("div", {"class": "content"})
        base_content = {}
        transaction_content = {}
        des_content = {}
        try:
            base_content = self.getContentByTags(contents[2]("li"))
            transaction_content = self.getContentByTags(contents[3]("li"))
            des_content = self.getContentByTags(contents[5]("div", {"class", "row"}))
            LOGGER.info(f"Successfully get house by url {url}")
        except Exception as e:
            LOGGER.error(f"Failed to get house by url {url}: {e}")

        house_base = schemas.HouseBase(
            url=url,
            sell_detail=sell_detail,
            base_content=base_content,
            transaction_content=transaction_content,
            des_content=des_content,
        )
        crud.createHouse(self.db, house_base)
        LOGGER.info("Successfully added house")


def main(max_page: int = 100):
    """main code

    Args:
        max_page (int, optional): max page to scrapy. Defaults to 100.
    """
    house = House()
    house.getData(max_page=max_page)


if __name__ == "__main__":
    main()
