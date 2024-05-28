from urllib.request import urlopen

from bs4 import BeautifulSoup


# set the url we want to visit
url = "https://www.opentable.com/metro/austin-restaurants"

# visit that url, and grab the html of said page
html = urlopen(url).read()

# we need to convert this into a soup object
soup = BeautifulSoup(html, 'html.parser', from_encoding="utf-8")

print(soup)


