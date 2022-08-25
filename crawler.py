import scrapy
import json
import pycountry
from scrapy.item import Item, Field
from geojson import Feature, Point, FeatureCollection, dump
import os
# from link_genarator import CustomLinkExtractor
import pipelines
from scrapy.spiders import CrawlSpider, Rule
from scrapy.link import Link
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
# from scrapy import log

# offset start from 0 +25
country = 'france'
# URL = f'https://www.booking.com/searchresults.en.html?ss={country}'
# url_format = 'https://www.booking.com/hotel'
# count = 0

# pycountry.countries.get(name='American Samoa').alpha_2


class LinkGenerator(LxmlLinkExtractor):
    def extract_links(self, response):
        json_response = json.loads(response.text)
        hotels = json_response['b_hotels']
        all_links = []
        if(len(hotels) > 0):
            bbox_list = get_list_of_bbox(response.url.split('BBOX=')[1])
            for bbox in bbox_list:
                all_links.append(Link(
                    f'https://www.booking.com/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEOuAEZyAEM2AED6AEB-AECiAIBqAIDuAKQzeKXBsACAdICJGRkNzM4YTFlLTg5ZWYtNDAzMC04MzJjLTI3YTk5ZTk0YzAzNdgCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=48cf466b7a980027&;aid=304142;dest_type=country;sr_id=;ref=searchresults;limit=100;stype=1;lang=he;ssm=1;sech=1;ngp=1;room1=A,A;maps_opened=1;esf=1;sr_countrycode=fr;sr_lat=;sr_long=;dba=1;dbc=1;srh=;somp=1;mdimb=1%20;tp=1%20;img_size=270x200%20;avl=1%20;nor=1%20;spc=1%20;rmd=1%20;slpnd=1%20;sbr=1;at=1%20;sat=1%20;ssu=1;srocc=1;BBOX={bbox}'))
        return all_links


def get_list_of_bbox(max_bbox):
    [min_lon, min_lat, max_lon, max_lat] = max_bbox.split(',')
    cent_lon = (float(min_lon) + float(max_lon))/2.0
    cent_lat = (float(min_lat) + float(max_lat))/2.0

    return [f'{min_lon},{min_lat},{cent_lon},{cent_lat}',
            f'{cent_lon},{min_lat},{max_lon},{cent_lat}',
            f'{min_lon},{cent_lat},{cent_lon},{max_lat}',
            f'{cent_lon},{cent_lat},{max_lon},{max_lat}']


class BookingSpider(CrawlSpider):
    base_url = 'https://www.booking.com'
    name = 'booking'
    custom_settings = {"ITEM_PIPELINES": {'pipelines.customImagePipeline': 1},
                       "IMAGES_STORE": 'hotels_images'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        "Content-Type": "application/x-www-form-urlencoded"}
    features = []

    rules = (Rule(LinkGenerator(allow='markers_on_map'), callback='parse_map'),)

    def start_requests(self):
        return [scrapy.Request('https://www.booking.com/country/fr.html', callback=self.parse_country)]

    def parse_country(self, response):
        max_bbox = response.xpath(
            '//script[contains(.,"b_map_google_bounding_box")]/text()').getall()[0].split(';')[1].split("= ")[1].replace("'", '')
        yield scrapy.Request(
            f'https://www.booking.com/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEOuAEZyAEM2AED6AEB-AECiAIBqAIDuAKQzeKXBsACAdICJGRkNzM4YTFlLTg5ZWYtNDAzMC04MzJjLTI3YTk5ZTk0YzAzNdgCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=48cf466b7a980027&;aid=304142;dest_type=country;sr_id=;ref=searchresults;limit=100;stype=1;lang=he;ssm=1;sech=1;ngp=1;room1=A,A;maps_opened=1;esf=1;sr_countrycode=fr;sr_lat=;sr_long=;dba=1;dbc=1;srh=;somp=1;mdimb=1%20;tp=1%20;img_size=270x200%20;avl=1%20;nor=1%20;spc=1%20;rmd=1%20;slpnd=1%20;sbr=1;at=1%20;sat=1%20;ssu=1;srocc=1;BBOX={max_bbox}',
            headers=self.headers)

        # return self.recursive_bbox_list(max_bbox)

        # for bbox in bbox_list:
        #     yield scrapy.Request(f'https://www.booking.com/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEOuAEZyAEM2AED6AEB-AECiAIBqAIDuAKQzeKXBsACAdICJGRkNzM4YTFlLTg5ZWYtNDAzMC04MzJjLTI3YTk5ZTk0YzAzNdgCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=48cf466b7a980027&;aid=304142;dest_type=country;sr_id=;ref=searchresults;limit=100;stype=1;lang=he;ssm=1;sech=1;ngp=1;room1=A,A;maps_opened=1;esf=1;sr_countrycode=fr;sr_lat=;sr_long=;dba=1;dbc=1;srh=;somp=1;mdimb=1%20;tp=1%20;img_size=270x200%20;avl=1%20;nor=1%20;spc=1%20;rmd=1%20;slpnd=1%20;sbr=1;at=1%20;sat=1%20;ssu=1;srocc=1;;BBOX={bbox}',
        #                          headers=self.headers, callback=self.parse_map)
        # print(
        #     f'https://www.booking.com/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEOuAEZyAEM2AED6AEB-AECiAIBqAIDuAKQzeKXBsACAdICJGRkNzM4YTFlLTg5ZWYtNDAzMC04MzJjLTI3YTk5ZTk0YzAzNdgCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=48cf466b7a980027&;aid=304142;dest_type=country;sr_id=;ref=searchresults;limit=100;stype=1;lang=he;ssm=1;sech=1;ngp=1;room1=A,A;maps_opened=1;esf=1;sr_countrycode=fr;sr_lat=;sr_long=;dba=1;dbc=1;srh=;somp=1;mdimb=1%20;tp=1%20;img_size=270x200%20;avl=1%20;nor=1%20;spc=1%20;rmd=1%20;slpnd=1%20;sbr=1;at=1%20;sat=1%20;ssu=1;srocc=1;;BBOX={bbox} !!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        # with open(f'{country}.txt', "a", encoding='utf8') as f:
        #     dump(bbox, f, ensure_ascii=False)
        #     f.write('\n')

    # def recursive_bbox_list(self, max_bbox):
    #     bbox_list = self.get_list_of_bbox(max_bbox)
    #     print(max_bbox, 'bbox!!')
    #     for bbox in bbox_list:
    #         yield scrapy.Request(
    #             f'https://www.booking.com/markers_on_map?label=gen173nr-1DCAIoTTgBSDNYBGhqiAEBmAEOuAEZyAEM2AED6AEB-AECiAIBqAIDuAKQzeKXBsACAdICJGRkNzM4YTFlLTg5ZWYtNDAzMC04MzJjLTI3YTk5ZTk0YzAzNdgCBOACAQ&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=48cf466b7a980027&;aid=304142;dest_type=country;sr_id=;ref=searchresults;limit=100;stype=1;lang=he;ssm=1;sech=1;ngp=1;room1=A,A;maps_opened=1;esf=1;sr_countrycode=fr;sr_lat=;sr_long=;dba=1;dbc=1;srh=;somp=1;mdimb=1%20;tp=1%20;img_size=270x200%20;avl=1%20;nor=1%20;spc=1%20;rmd=1%20;slpnd=1%20;sbr=1;at=1%20;sat=1%20;ssu=1;srocc=1;BBOX={bbox}',
    #             headers=self.headers, callback=self.parse_map)
    #         yield from self.recursive_bbox_list(bbox)

    def _requests_to_follow(self, response):
        # if not isinstance(response, HtmlResponse):
        #     return
        seen = set()
        for rule_index, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            for link in rule.process_links(links):
                seen.add(link)
                request = self._build_request(rule_index, link)
                yield rule.process_request(request, response)

    def parse_map(self, response):
        json_response = json.loads(response.text)
        with open(f'country.txt', "a", encoding='utf8') as f:
            f.write(response.url)
            f.write('\n')
        hotels = json_response['b_hotels']

        for hotel in hotels:
            hotel_url = self.base_url + hotel['b_url']
            with open(f'{country}.txt', "a", encoding='utf8') as f:
                f.write(hotel_url)
                f.write('\n')
            # yield scrapy.Request(hotel_url, self.pasre_hotel)

    def pasre_hotel(self, hotel):
        try:
            properties = {}
            coordinates = hotel.xpath(
                '//script[contains(.,"defaultCoordinates")]/text()').getall()[0].split('function')[3].split('defaultCoordinates: [')[1].split('],')[0]
            coordinates = coordinates.replace("'", '').split(',')
            x = coordinates[0].strip()
            y = coordinates[1].strip()
            point = Point((float(y), float(x)))

            hotel_name = hotel.css("#hp_hotel_name_reviews::text").get().replace('\n', '')
            properties['hotel_name'] = hotel_name

            hotel_address = hotel.css(
                '#showMap2 .hp_address_subtitle .ltr::text').get().replace('\n', '')
            properties['hotel_address'] = hotel_address

            hotel_descrption = hotel.css(
                '#property_description_content p::text').getall()
            properties['hotel_descrption'] = ''.join(hotel_descrption)

            hotel_rate = hotel.css('[data-testid="review-score-component"] div::text').get()
            properties['hotel_rate'] = hotel_rate

            number_of_stars = len(hotel.css('[data-testid = "rating-stars"] span').getall())
            properties['number_of_stars'] = number_of_stars

            events = {}
            events_near_hotel = hotel.css(
                '.property_page_surroundings_block .bui-list__item .bui-list__body')
            for event in events_near_hotel[1:]:
                event_key = event.css(
                    '.bui-list__description::text').get().replace('\n', '')
                event_value = event.css(
                    '.hp_location_block__section_list_distance::text').get().replace('\n', '')
                events[event_key] = event_value
            properties['events_near_hotel'] = events

            hotel_services = hotel.css('.hotel-facilities-group')
            services = {}
            for service in hotel_services:
                service_key = service.css(
                    '.hotel-facilities-group__title-text::text').getall()[1].replace('\n', '')
                # print('service key: %s' % service_key)
                services[service_key] = []
                service_items = service.css('.hotel-facilities-group__list-item')
                for item in service_items:
                    service_value = item.css(
                        '.bui-list__body .bui-list__description::text').get().replace('\n', '')
                    services[service_key].append(service_value)
                # hotel-facilities-group__policy in case of no list
            properties['hotel_services'] = services

            hotel_comments = hotel.css('.c-review__body--original::text').getall()
            first_comment = hotel_comments[0]
            second_comment = hotel_comments[1]
            properties['hotel_comments'] = f'first_comment:{first_comment}. second_comment: {second_comment}'

            image_urls = hotel.css('.active-image img ::attr(src)').getall()

            feature = Feature(geometry=point, properties=properties)
            self.features.append(feature)

            yield {'image_urls': image_urls, "hotel_name": hotel_name}

        except Exception as e:
            print(f'An exception occurred: {e}')

    # def closed(self, reason):
    #     feature_collection = FeatureCollection(self.features)
    #     with open(f'{country}.geojson', "w", encoding='utf8') as f:
    #         dump(feature_collection, f, ensure_ascii=False)


# class BookingSpider(CrawlSpider):
#     name = 'booking'
#     # start_urls = [
#     #     'https://www.booking.com/searchresults.en.html?ss=france&dest_type=country&offset=0']
#     def start_ = ['https://www.booking.com/country/fr.html']
#     rules = (
#         Rule(LinkExtractor(allow=f'https://www.booking.com/hotel/',
#             deny='https://www.booking.com/hotel/index.html'), callback='parse_hotels'),
#     )

#     def parse_hotels(self, response):
#         hotel_name = response.css("#hp_hotel_name_reviews::text").get()
#         print(hotel_name,'hgiii')
#         # with open(f'{country}.txt','w') as f:
#         #     f.write(hotel_name)


# # print(f'number of results: {count}')
