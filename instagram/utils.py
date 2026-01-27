from http.cookies import SimpleCookie

from dotenv import dotenv_values


def cookie_parse():
    cookie_string = dotenv_values(".env")["INSTAGRAM_COOKIES"]

    cookie = SimpleCookie()
    cookie.load(cookie_string)

    cookies = {}

    for key, value in cookie.items():
        cookies[key] = value.value

    return cookies
