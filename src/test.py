from bs4 import BeautifulSoup

with open("hh.html", "r") as f:
    soup = BeautifulSoup(f.read(), "lxml")
    print(soup.select('adno') == [])
