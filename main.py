#!/usr/bin/python

from discord_webhook import DiscordWebhook, DiscordEmbed
from bs4 import BeautifulSoup
import requests as req
import hashlib
import urllib3
import json
import time
import re


urllib3.disable_warnings()  # // sweating

DEBUG = True
URL = "https://www.reg.chula.ac.th/th/"

config = json.load(open("config.json", "r"))
webhook_urls = config["DEBUG_WEBHOOK_URLS"] if DEBUG else config["WEBHOOK_URLS"]


class Article:
    def __init__(self, name: str, url: str, img: str):
        self.name = name
        self.url = url
        self.img = re.sub(r"-\d{3}x\d{3}", "", img)
        self.date = None

    def to_png(self) -> None:
        # Image on Chula website is using .jpg ...
        # WHY? WHY? WHY? WHY? WHY? WHY? WHY?
        # anyways, discord said "we only accept .png" so now i gotta download
        # this shit and convert it haha.

        with open("img.png", "wb") as f:
            # This is the worst code I have ever written in my life
            f.write(req.get(self.img, verify=False).content)

    def to_hash(self) -> str:
        m = hashlib.sha256()
        m.update(bytes(self.name, 'utf-8'))
        m.update(bytes(self.url, 'utf-8'))
        return m.hexdigest()

    def __repr__(self) -> str:
        return f"Article({self.name=})"

    def __hash__(self) -> int:
        return int(self.to_hash(), 16)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Article):
            return self.to_hash() == value.to_hash()
        return False


r = req.get(url=URL, verify=False)
soup = BeautifulSoup(r.text, "html.parser")

articles: list[Article] = []

for div in soup.find_all("li", {"class": "wp-block-post"}):
    for img in div.find_all("img", alt=True):
        articles.append(
            Article(img['alt'], img.parent['href'], img['src'])
        )

index = 0
for div in soup.find_all("div", {"class": "wp-block-post-date"}):
    articles[index].date = div.time["datetime"]
    index += 1


old_articles: list[str] = json.load(open('articles.json', 'r')) or []
new_articles = list(set(i for i in articles if i.to_hash() not in old_articles))

print(f"Found {len(new_articles)} new articles!")

for webhook_url in webhook_urls:
    for article in new_articles:
        webhook = DiscordWebhook(url=webhook_url)

        article.to_png()
        with open('img.png', "rb") as f:
            webhook.add_file(file=f.read(), filename="img.png")

        embed = DiscordEmbed(color="de5c8e")
        embed.set_author(name=article.name, url=article.url)
        embed.set_image(url="attachment://img.png")
        # https://github.com/lovvskillz/python-discord-webhook/blob/master/discord_webhook/webhook.py#L90
        embed.timestamp = article.date

        if DEBUG:
            embed.set_title("- DEBUG MODE -")

        webhook.add_embed(embed)

        webhook.execute()
        time.sleep(3)

        if DEBUG:
            break


# Save
json.dump([article.to_hash() for article in articles], open("articles.json", "w"))
