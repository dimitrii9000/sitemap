#
#               Sitemap generator
#               Python v3.7.2
#

import json
import requests
from bs4 import BeautifulSoup
import multiprocessing
import time
import XMLS
import files
import urllib.parse
import header


class SiteMapGenerator:

    def __init__(self):
        with open("config.json", 'r') as f:
            self.config_file = json.load(f)
        self.main_address = self.config_file['site_address']
        self.output_file_name = self.config_file['output_file_name']
        self.workers = self.config_file['workers']
        self.visited_links = []
        self.session = requests.Session
        self.session.headers = header.header

    def wrap_url(self, url):
        wrapped_url = XMLS.URL_XML % url
        return wrapped_url

    def run(self):
        # Переменная, куда сохраняются все обернутые url-ы
        xml = ''
        not_visited_urls = [self.main_address]
        pool = multiprocessing.Pool(self.workers)

        while len(not_visited_urls) != 0:

            print("Количество непосещенных ссылок = ", len(not_visited_urls))
            print("Количество посещенных ссылок = ", len(self.visited_links))

            results = pool.map(self.process_each_url, not_visited_urls)
            for result in results:
                found_links = result[0]
                url = result[1]
                not_visited_urls.remove(url)
                self.visited_links.append(url)
                xml += self.wrap_url(url)

                for l in found_links:
                    if l not in self.visited_links and l not in not_visited_urls:
                        not_visited_urls.append(l)

        pool.close()
        pool.join()

        with open(self.output_file_name, 'w', encoding="utf-8") as f:
            f.write(XMLS.SITEMAP_HEADER)
            f.write(xml)
            f.write(XMLS.SITEMAP_FOOTER)

    def process_each_url(self, url):
        links = []
        # Если расширение страницы в списке исключаемых файлов, записываем ее, но не используем дальше
        if url.split('.')[-1] in files.f:
            return [links, url]
        try:
            content = self.session().get(url).text
        except TimeoutError or requests.exceptions.ConnectionError:
            content = ''

        bsoup = BeautifulSoup(content, features="html.parser")
        hrefs = bsoup.find_all('a', href=True)

        for h in hrefs:
            link = h['href']
            link = self.if_link(link)

            if link is not None and link not in links:
                links.append(link)
        return [links, url]

    def if_link(self, url):
        # Юникодим русские и не только символы в ссылке
        url = urllib.parse.unquote(url)
        # Если ссылка не пустая, не GET, не якорь и не в исключениях
        if url != '' and '#' not in url and '?' not in url:
            if len(url) > 300:
                return None
            # Хэндлим относительные ссылки
            if url[0] == '/':
                url = self.main_address[:len(self.main_address)-1] + url
            # Отсеиваем не ссылки
            elif url[:4] != 'http':
                return None
            # Проверяем, не является ли ссылка ссылкой на внешний ресурс
            if url.split('/')[2] == self.main_address.split('/')[2]:
                return url
            else:
                return None
        else:
            return None


if __name__ == '__main__':
    smg = SiteMapGenerator()
    smg.run()
    print('--------------------------------------------------------------')
    print("Время выполнения составило: {} c.".format(time.perf_counter()))
    print("Количество сохраненных ссылок = {}".format(len(smg.visited_links)))
    print("Результаты проверки сохранены в: {}".format(smg.output_file_name))
    print('--------------------------------------------------------------')
