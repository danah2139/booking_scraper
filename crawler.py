import scrapy
import json
from country_bounding_boxes import country_subunits_by_iso_code
from scrapy.item import Item, Field
from geojson import Feature, Point, FeatureCollection, dump
import os
# from link_genarator import CustomLinkExtractor
import pipelines
from scrapy.spiders import CrawlSpider, Rule
from scrapy.link import Link
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
country = 'israel'
base_url = 'https://www.booking.com'
markers_on_map_url = base_url+'/markers_on_map?aid=304142&aid=304142&label=gen173nr-1DCAQoggJCDXNlYXJjaF9pc3JhZWxICVgEaGqIAQGYAQm4ARnIAQzYAQPoAQH4AQaIAgGoAgO4Ap3crZgGwAIB0gIkMWM5YzQ2ZTktMWVkZS00Y2E4LTlhMWYtZmU0MmNmMjkyNGMx2AIE4AIB&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=47f45f0e5e5301fc&dest_id=103&dest_type=&sr_id=&ref=searchresults&limit=100&stype=1&lang=en-gb&ssm=1&sech=1&ngp=1&room1=A%2CA&maps_opened=1&esf=1&nflt=ht_id%3D204&sr_countrycode=il&sr_lat=&sr_long=&dba=1&dbc=1&srh=3626681%2C7917430%2C8245116%2C8263881%2C1309762%2C8950327%2C8698987%2C3564377%2C6960843%2C8289428%2C8156848%2C6959499%2C8601421%2C8950938%2C7177203%2C8445244&somp=1&mdimb=1%20&tp=1%20&img_size=270x200%20&avl=1%20&nor=1%20&spc=1%20&rmd=1%20&slpnd=1%20&sbr=1&at=1%20&sat=1%20&ssu=1&srocc=1;BBOX='


# pycountry.countries.get(name='American Samoa').alpha_2
class LinkGenerator(LxmlLinkExtractor):
    def extract_links(self, response):
        json_response = json.loads(response.text)
        hotels = json_response['b_hotels']
        all_links = []
        if(len(hotels) > 0):
            bbox_list = get_list_of_bbox(response.url.split('BBOX=')[1])
            for bbox in bbox_list:
                all_links.append(Link(markers_on_map_url+bbox))
        return all_links


def get_list_of_bbox(max_bbox):
    """
    dividing bounding box to 4 boxes with equal areas 
    """
    [min_lon, min_lat, max_lon, max_lat] = max_bbox.split(',')
    cent_lon = (float(min_lon) + float(max_lon))/2.0
    cent_lat = (float(min_lat) + float(max_lat))/2.0

    return [f'{min_lon},{min_lat},{cent_lon},{cent_lat}',
            f'{cent_lon},{min_lat},{max_lon},{cent_lat}',
            f'{min_lon},{cent_lat},{cent_lon},{max_lat}',
            f'{cent_lon},{cent_lat},{max_lon},{max_lat}']


class BookingSpider(CrawlSpider):
    name = 'booking'
    custom_settings = {"ITEM_PIPELINES": {'pipelines.customImagePipeline': 1},
                       "IMAGES_STORE": 'hotels_images', 'LOG_LEVEL': 'INFO', 'CONCURRENT_REQUESTS': 1000,
                       'CONCURRENT_REQUESTS_PER_DOMAIN': 800, 'DOWNLOAD_DELAY': 0.1}
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        "Content-Type": "application/x-www-form-urlencoded"}
    features = []
    count_hotels = 0

    rules = (Rule(LinkGenerator(allow='markers_on_map'),
                  callback='parse_map', follow=True),)

    def start_requests(self):
        # return [scrapy.Request(base_url+'/country/il.html', callback=self.parse_country, headers=self.headers)]
        max_bbox = [c.bbox for c in country_subunits_by_iso_code('il')]
        max_bbox = str(max_bbox)[2:-2].replace(' ', '')
        yield scrapy.Request(markers_on_map_url+max_bbox, headers=self.headers)

    # def parse_country(self, response):
    #     # max_bbox = response.xpath(
    #     #     '//script[contains(.,"b_map_google_bounding_box")]/text()').getall()[0].split(';')[1].split("= ")[1].replace("'", '')
    #     max_bbox = [c.bbox for c in country_subunits_by_iso_code('il')]
    #     max_bbox = str(max_bbox)[2:-2].replace(' ', '')
    #     yield scrapy.Request(markers_on_map_url+max_bbox, headers=self.headers)

    def _requests_to_follow(self, response):
        """
        Override the requests_to_follow function from CrawlSpider to allow link
        extraction from all files.
        """
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
        hotels = json_response['b_hotels']
        for hotel in hotels:
            link_hotel = hotel['b_url']
            if(link_hotel.split('hotel/')[1][0:2] != 'il'):
                return
            hotel_url = base_url + link_hotel
            # with open(f'{country}.txt', "a", encoding='utf8') as f:
            #     f.write(hotel_url)
            #     f.write('\n')
            yield scrapy.Request(hotel_url, self.pasre_hotel)

    def pasre_hotel(self, hotel):
        try:
            # with open('country.txt', "a", encoding='utf8') as f:
            #     f.write(hotel.url)
            #     f.write('\n')
            self.count_hotels += 1
            self.logger.info('hotel number: %s hotel url: %s', self.count_hotels, hotel.url)
            properties = {}
            coordinates = hotel.xpath(
                '//script[contains(.,"defaultCoordinates")]/text()').getall()[0].split('function')[3].split('defaultCoordinates: [')[1].split('],')[0]
            coordinates = coordinates.replace("'", '').split(',')
            x = coordinates[0].strip()
            y = coordinates[1].strip()
            point = Point((float(y), float(x)))

            hotel_name = hotel.css(
                "#hp_hotel_name_reviews::text").get()
            hotel_name = hotel_name.replace('\n', '') if hotel_name else 'None'
            properties['hotel_name'] = hotel_name

            hotel_address = hotel.css(
                '#showMap2 .hp_address_subtitle span::text').get()
            hotel_address = hotel_address.replace('\n', '') if hotel_address else'None'
            properties['hotel_address'] = hotel_address

            hotel_descrption = hotel.css(
                '#property_description_content p::text').getall()
            properties['hotel_descrption'] = ''.join(hotel_descrption)

            hotel_rate = hotel.css(
                '[data-testid="review-score-component"] div::text').get()
            properties['hotel_rate'] = hotel_rate

            number_of_stars = len(hotel.css('[data-testid = "rating-stars"] span').getall())
            properties['number_of_stars'] = number_of_stars

            events = {}
            events_near_hotel = hotel.css(
                '.property_page_surroundings_block .bui-list_item .bui-list_body')
            for event in events_near_hotel[1:]:
                event_key = event.css(
                    '.bui-list__description::text').get()
                event_key = event_key.replace('\n', '') if event_key else 'None'
                event_value = event.css(
                    '.hp_location_block__section_list_distance::text').get().replace('\n', '')
                event_value = event_value.replace('\n', '') if event_value else 'None'
                events[event_key] = event_value
            properties['events_near_hotel'] = events

            hotel_services = hotel.css('.hotel-facilities-group')
            services = {}
            for service in hotel_services:
                service_key = service.css(
                    '.hotel-facilities-group__title-text::text').getall()[1]
                service_key = service_key.replace('\n', '') if service_key else 'None'
                # print('service key: %s' % service_key)
                service_value = service.css(
                    '.hotel-facilities-group__policy::text').get()
                if(service_value):
                    services[service_key] = service_value.replace('\n', '')
                else:
                    services[service_key] = []
                    service_items = service.css(
                        '.hotel-facilities-group__list-item')
                    for item in service_items:
                        service_value = item.css(
                            '.bui-list_body .bui-list_description::text').get()
                        service_value = service_value.replace('\n', '') if service_value else 'None'
                        services[service_key].append(service_value)
                properties['hotel_services'] = services

            hotel_comments = hotel.css(
                '.c-review__body--original::text').getall()
            first_comment = hotel_comments[0] if len(hotel_comments) > 0 else 'None'
            second_comment = hotel_comments[1] if len(hotel_comments) > 1 else 'None'
            properties['hotel_comments'] = f'first_comment:{first_comment}. second_comment: {second_comment}'

            image_urls = hotel.css('.active-image img ::attr(src)').getall()

            feature = Feature(geometry=point, properties=properties)
            self.features.append(feature)

            yield {'image_urls': image_urls, "hotel_name": hotel_name}

        except Exception as e:
            print(f'An exception occurred: {e}')

    def closed(self, reason):
        feature_collection = FeatureCollection(self.features)
        with open(f'{country}.geojson', "w", encoding='utf8') as f:
            dump(feature_collection, f, ensure_ascii=False)
