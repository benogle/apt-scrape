import scraper


#phone re

m = scraper.CraigslistScraper.PHONE_RE.search('(509) 123 - 4532')
assert m
assert m.group(1) == '509' and m.group(3) == '123' and m.group(5) == '4532'

m = scraper.CraigslistScraper.PHONE_RE.search('509-123-4532')
assert m
assert m.group(1) == '509' and m.group(3) == '123' and m.group(5) == '4532'

m = scraper.CraigslistScraper.PHONE_RE.search('509 . 123 .4532')
assert m
assert m.group(1) == '509' and m.group(3) == '123' and m.group(5) == '4532'



db = scraper.DB()

print db.hasApartment('1328891860')

print db.getArea('SOMA / south beach')