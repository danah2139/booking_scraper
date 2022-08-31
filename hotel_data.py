from geojson import Feature, Point, FeatureCollection, dump


class HotelData:
    properties = {}

    def __init__(self):
        self.get_coordinates()
        self.get_hotel_name()

    def get_coordinates(self, hotel):
        coordinates = hotel.xpath(
            '//script[contains(.,"defaultCoordinates")]/text()').getall()[0].split('function')[3].split('defaultCoordinates: [')[1].split('],')[0]
        coordinates = coordinates.replace("'", '').split(',')
        x = coordinates[0].strip()
        y = coordinates[1].strip()
        point = Point((float(y), float(x)))

    def get_hotel_name(self, hotel):
        hotel_name = hotel.css(
            "#hp_hotel_name_reviews::text").get()
        hotel_name = hotel_name.replace('\n', '') if hotel_name else 'None'
        self.properties['hotel_name'] = hotel_name
