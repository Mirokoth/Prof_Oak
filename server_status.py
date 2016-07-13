import requests
from bs4 import BeautifulSoup

_page = requests.get(
                'http://www.mmoserverstatus.com/pokemon_go',
                timeout=120)

_page.text
_page_cont = _page.content
_soup_page = BeautifulSoup(_page_cont)
_soup_li = _soup_page.find_all("li", "white")
if 'fa fa-check' in str(_soup_li[0]):
    print("Server up")
else:
    print('cant find green')
print(_soup_li[0])
#print(_soup_li)
#print(_soup_page)
