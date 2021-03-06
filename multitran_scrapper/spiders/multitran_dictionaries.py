# -*- coding: utf-8 -*-
"""
It's a parser which find connection between abbreviation and full name of dictionary

DONE:
 - Input/Output
 - Go to every dictionary and find full name and abbreviation

TO DO:
 - All is already done, you should only run the spider
 - Maybe rewrite code for use Pandas as table engine instead of csv (optional)

It has not input csv file.

For every word from input file, the parser creates several columns of information and saves to output csv file:
  abbreviation | full name

Algorithms:
 - Firstly, the parser finds all links on dictionaries and go to everyone (dictionaries have only full name in main page)
 - For any dictionary, go to first word from it.
    It based on think that all words from any dictionary contatins translations from the dictionary.
 - For word finds all dictionaries (page with translation contains only abbreviations) and link on them which contains full name


## Parsing speed increasing (important settings):
For it, you should change settings.py.
The Scrapy is based on asynchronous framework Twisted. Please see good lecture about async http://cs.brown.edu/courses/cs168/s12/handouts/async.pdf
So Twisted has several flows. Flows are conditionally "concurrent".
And so settings.py includes CONCURRENT_REQUESTS. It's count of flows. And you should set it.
Of course, bigger CONCURRENT_REQUESTS provides big speed, but it can creates some errors, for example TimeError.
With big speed the parser tries to download many links simultaneously and someone can stuck.
When time is not critical, you should set CONCURRENT_REQUESTS < 16 otherwise > 16.
For timeout error solving, you can increase DOWNLOAD_TIMEOUT (in sec).

Also you can except some dictionaries for some narrow parsing using EXCEPTED_DICTIONARIES (dictionary abbreviation list).

"""
import csv

import scrapy
from scrapy import Request

# Settings
# Delimiter and quotechar are parameters of csv file. You should know it if you created the file
CSV_DELIMITER = '	'
CSV_QUOTECHAR = '"'  # '|'
OUTPUT_CSV_NAME = 'output_dictionaries_abbreviations.csv'  # Path to output file with csv type
TRANSLATE_WORD_INDEX = 0  # Index of column which should be translated. Others columns will be copied to output file
EXCEPTED_DICTIONARIES = ['Сленг', 'Разговорное выражение', 'табу']  # Dictionaries which shouldn't be in output


class MultitranSpider(scrapy.Spider):
    """
    This spider parses all dictionaries and finds corresponding reduction
    """
    name = "multitran_dictionaries"
    allowed_domains = ["multitran.com"]
    start_urls = ['http://www.multitran.com/m.exe?CL=1&s&l1=1&l2=2&SHL=2']

    def __init__(self):
        self.output_file = open(OUTPUT_CSV_NAME, 'w')
        self.output_writer = csv.writer(self.output_file, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR,
                                        quoting=csv.QUOTE_ALL)
        self.output = []

    def parse(self, response):
        dict_xpath = '//*/tr/td[@width=110]/a/@href'
        # i = 0
        for dictionaries in response.xpath(dict_xpath):
            # print(i)
            # i += 1
            yield Request("http://multitran.com{}&SHL=2".format(dictionaries.extract()), callback=self.parse_dict)

    def parse_dict(self, response):
        # print(response.url)
        dict_name = response.xpath('//*/td/b/text()').extract()[0]
        # self.output_writer.writerow([])
        # print()
        if response.meta.get("dict_abbr", None) is not None:
            # dict_name = response.xpath('//*/tr[1]/td[@class="termsforsubject"][1]/a/@href').extract()[0]
            row = [response.meta.get("dict_abbr").split(",")[0], dict_name]
            if not "|".join(row) in self.output:
                self.output_writer.writerow(row)
                self.output.append("|".join(row))
        else:
            url = "http://multitran.com{}&SHL=2".format(
                response.xpath('//*/tr/td[@class="termsforsubject"][1]/a/@href').extract()[0])
            # print(url)
            yield Request(url=url, callback=self.parse_word,
                          meta={"dict_name": dict_name, 'prev_url': response.url})

    def parse_word(self, response):
        # self.output_writer.writerow([response.meta['dict_name'], response.meta['prev_url'], response.url])
        dict_xpath = '//*/td[@class="subj"]/a'
        for d in response.xpath(dict_xpath):
            name = d.xpath("text()").extract()[0]
            url = "http://multitran.com{}&SHL=2".format(d.xpath("@href").extract()[0])
            yield Request(url=url, callback=self.parse_dict,
                          meta={"dict_abbr": name})

    def close(self, reason):
        self.output_file.close()
