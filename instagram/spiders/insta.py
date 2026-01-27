import json

import scrapy

from ..utils import cookie_parse


class InstaSpider(scrapy.Spider):
    name = "insta"
    allowed_domains = ["www.instagram.com"]
    headers = {
        "x-asbd-id": 198387,
        "x-csrftoken": "gqeYY9dr1dCwfvtyZCgy88tcMn1A2N85",
        "x-ig-app-id": 936619743392459,
        "x-requested-with": "XMLHttpRequest",
    }
    username = str(input("Enter Instagram username: "))

    async def start(self):
        yield scrapy.Request(
            url=f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}",
            cookies=cookie_parse(),
            headers=self.headers,
            callback=self.parse,
        )

    def parse(self, response):
        resp = json.loads(response.body)
        user_data = resp["data"]["user"]
        full_name = user_data["full_name"]
        bio = user_data["biography"]
        bio_link = user_data["bio_links"]

        user = {
            "id": user_data["id"],
            "username": user_data["username"],
            "full_name": full_name,
            "category": user_data["category_name"],
            "posts": user_data["edge_owner_to_timeline_media"]["count"],
            "followers": user_data["edge_followed_by"]["count"],
            "following": user_data["edge_follow"]["count"],
            "profile_picture": user_data["profile_pic_url_hd"],
            "no. of highlights": user_data["highlight_reel_count"],
            "bio": self.format_bio(bio),
            "bio link": self.get_bio_link(bio_link),
        }
        for k, v in user.items():
            print(f"{k:<10}: {v}")
        yield user_data

    def format_bio(self, bio: str):
        return bio.replace("\n", f"\n{'':<12}")

    def get_bio_link(self, bio_link):
        if not bio_link == []:
            url = bio_link[0]["url"]
            return url
