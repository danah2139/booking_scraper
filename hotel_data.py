from geojson import Feature, Point, FeatureCollection, dump


class HotelData:
    properties = {}

    def __init__(self, name):
        self.name = name

    def get_coordinates(self, hotel):
        coordinates = hotel.xpath(
            '//script[contains(.,"defaultCoordinates")]/text()').getall()[0].split('function')[3].split('defaultCoordinates: [')[1].split('],')[0]
        coordinates = coordinates.replace("'", '').split(',')
        x = coordinates[0].strip()
        y = coordinates[1].strip()
        point = Point((float(y), float(x)))
