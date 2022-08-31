import scrapy
import json
from country_bounding_boxes import country_subunits_by_iso_code
from geojson import Feature, Point, FeatureCollection, dump
from hotel_data import HotelData
import pycountry
import pipelines
from scrapy.spiders import CrawlSpider, Rule
from scrapy.link import Link
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor

country = input('please enter country name:')
iso_code = pycountry.countries.get(name=country).alpha_2
base_url = 'https://www.booking.com'
markers_on_map_url = base_url+'/markers_on_map?aid=304142&aid=304142&label=gen173nr-1DCAQoggJCDXNlYXJjaF9pc3JhZWxICVgEaGqIAQGYAQm4ARnIAQzYAQPoAQH4AQaIAgGoAgO4Ap3crZgGwAIB0gIkMWM5YzQ2ZTktMWVkZS00Y2E4LTlhMWYtZmU0MmNmMjkyNGMx2AIE4AIB&sid=5d1d00651882df1251e4de2b42a91f58&srpvid=47f45f0e5e5301fc&dest_type=&sr_id=&ref=searchresults&limit=100&stype=1&lang=en-gb&ssm=1&sech=1&ngp=1&room1=A%2CA&maps_opened=1&esf=1&nflt=ht_id%3D204&sr_countrycode=il&sr_lat=&sr_long=&dba=1&dbc=1&srh=3626681%2C7917430%2C8245116%2C8263881%2C1309762%2C8950327%2C8698987%2C3564377%2C6960843%2C8289428%2C8156848%2C6959499%2C8601421%2C8950938%2C7177203%2C8445244&somp=1&mdimb=1%20&tp=1%20&img_size=270x200%20&avl=1%20&nor=1%20&spc=1%20&rmd=1%20&slpnd=1%20&sbr=1&at=1%20&sat=1%20&ssu=1&srocc=1;BBOX='


class LinkGenerator(LxmlLinkExtractor):
    def extract_links(self, response):
        json_response = json.loads(response.text)
        hotels = json_response['b_hotels']
        all_links = []
        if(len(hotels) > 1):
            bbox = response.url.split('BBOX=')[1]
            bbox_list = devide_bbox(bbox)
            for bbox in bbox_list:
                all_links.append(Link(markers_on_map_url+bbox))
        return all_links


def devide_bbox(bbox):
    """
    dividing bounding box to 4 boxes with equal areas 
    """
    [min_lon, min_lat, max_lon, max_lat] = bbox.split(',')
    cent_lon = (float(min_lon) + float(max_lon))/2.0
    cent_lat = (float(min_lat) + float(max_lat))/2.0

    return [f'{min_lon},{min_lat},{cent_lon},{cent_lat}',
            f'{cent_lon},{min_lat},{max_lon},{cent_lat}',
            f'{min_lon},{cent_lat},{cent_lon},{max_lat}',
            f'{cent_lon},{cent_lat},{max_lon},{max_lat}']


class BookingSpider(CrawlSpider):
    name = 'booking'
    custom_settings = {"ITEM_PIPELINES": {'pipelines.customImagePipeline': 1},
                    "IMAGES_STORE": 'hotels_images', 'LOG_LEVEL': 'INFO'}
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    features = []
    count_hotels = 0

    rules = (Rule(LinkGenerator(allow='markers_on_map'),
                callback='parse_map', follow=True),)

    def start_requests(self):
        country_bbox = [c.bbox for c in country_subunits_by_iso_code(iso_code)]
        country_bbox = str(country_bbox)[2:-2].replace(' ', '')
        yield scrapy.Request(markers_on_map_url + country_bbox)

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
            yield scrapy.Request(hotel_url, self.parse_hotel)

    def parse_hotel(self, hotel):
        try:
            self.count_hotels += 1
            hotel_url = hotel.url.split('?')[0]
            self.logger.info('hotel number:%s ,hotel url: %s',self.count_hotels,hotel_url)
            hotel_data = HotelData()
            image_urls = hotel_data.get_hotel_images_url(hotel)
            hotel_name = hotel_data.get_hotel_name(hotel)
            properties = hotel_data.push_hotel_data_to_properties(hotel)
            hotel_coordinates = hotel_data.get_hotel_coordinates(hotel)
            point = Point(hotel_coordinates)
            feature = Feature(geometry=point, properties=properties)
            self.features.append(feature)
            yield {'image_urls':image_urls,"hotel_name":hotel_name }

        except Exception as e:
            self.logger.info(f'An exception occurred: {e}')

    def closed(self, reason):
        feature_collection = FeatureCollection(self.features)
        with open(f'{country}.geojson', "w", encoding='utf8') as f:
            dump(feature_collection, f, ensure_ascii=False)
