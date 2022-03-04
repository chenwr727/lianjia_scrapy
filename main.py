import codecs
import re
import time

import bs4
import demjson
import pandas as pd
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
        self.writeHtml()
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
            self.getHouseByUrl(url)
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

    def writeHtml(self):
        def change(x):
            if isinstance(x, str):
                room = x.split("室")[0]
                if len(room) == 1 and room in "12345":
                    return int(room)
                return 6
            return 0

        df = pd.read_sql(crud.getHouseStatement(self.db), self.db.bind)
        columns = ["经纬度", "小区", "面积", "总价", "均价", "房屋户型", "网址"]
        df.columns = columns
        df.sort_values(by="总价", ascending=False, inplace=True)
        df["经度"] = df["经纬度"].map(lambda x: x.split(",")[0])
        df["纬度"] = df["经纬度"].map(lambda x: x.split(",")[1])
        df["地址"] = df[["经度", "纬度", "小区"]].apply(
            lambda x: "%s,%s,'%s'" % (x["经度"], x["纬度"], x["小区"]), axis=1
        )
        df["信息"] = df[["房屋户型", "面积", "总价"]].apply(
            lambda x: "%s\t%s平米\t%s万" % (x["房屋户型"], x["面积"], x["总价"]), axis=1
        )
        df_group = (
            df.groupby("地址")
            .agg(
                {
                    "信息": lambda x: ",".join(map(lambda y: "'%s'" % y, x)),
                    "网址": lambda x: ",".join(map(lambda y: "'%s'" % y, x)),
                }
            )
            .reset_index()
        )
        df_house = pd.merge(left=df[["地址", "总价", "房屋户型"]], right=df_group, on="地址")
        df_house["房屋户型"] = df_house["房屋户型"].map(change)
        price_df = df_house.apply(
            lambda x: "[%s,%s,%s,[%s],[%s]]"
            % (x["地址"], x["总价"], x["房屋户型"], x["信息"], x["网址"]),
            axis=1,
        )
        data_str = "var points = [" + ",".join(price_df) + "];\n"
        with open("house_xm_base.html", "r", encoding="utf-8") as f:
            s = f.read()
        with codecs.open("house_xm.html", "w", "utf-8") as f:
            f.write(s.replace("// 值写入", data_str))
        LOGGER.info("Successfully writed html")


def main(max_page: int = 100):
    """main code

    Args:
        max_page (int, optional): max page to scrapy. Defaults to 100.
    """
    house = House()
    house.getData(max_page=max_page)


if __name__ == "__main__":
    main()
