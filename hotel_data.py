class HotelData:
    def __init__(self):
        self.properties = {}

    def get_hotel_coordinates(self, hotel):
        coordinates = hotel.xpath(
            '//script[contains(.,"defaultCoordinates")]/text()').getall()[0].split('defaultCoordinates: [')[1]
        coordinates = coordinates.split('],')[0].replace("'", '').split(',')
        x = coordinates[0].strip()
        y = coordinates[1].strip()
        return (float(y), float(x))

    def get_hotel_name(self, hotel):
        hotel_name = hotel.css(
            "#hp_hotel_name_reviews::text").get()
        hotel_name = hotel_name.replace('\n', '') if hotel_name else 'None'
        return hotel_name
    
    def get_hotel_address(self, hotel):
        hotel_address = hotel.css(
            '#showMap2 .hp_address_subtitle span::text').get()
        hotel_address = hotel_address.replace(
            '\n', '') if hotel_address else'None'
        return hotel_address
        
    def get_hotel_description(self, hotel):
        hotel_descrption = hotel.css(
            '#property_description_content p::text').getall()
        return ''.join(hotel_descrption)
    
    def get_hotel_rate(self, hotel):
        hotel_rate = hotel.css(
        '[data-testid="review-score-component"] div::text').get()
        return hotel_rate
    
    def get_hotel_number_of_stars(self, hotel):
        number_of_stars = len(
            hotel.css('[data-testid = "rating-stars"] span').getall())
        return number_of_stars
    
    def get_hotel_events(self, hotel):
        events = {}
        events_near_hotel = hotel.css(
            '.property_page_surroundings_block .bui-list_item .bui-list_body')
        for event in events_near_hotel[1:]:
            event_key = event.css(
                '.bui-list__description::text').get()
            event_key = event_key.replace(
                '\n', '') if event_key else 'None'
            event_value = event.css(
                '.hp_location_block__section_list_distance::text').get().replace('\n', '')
            event_value = event_value.replace(
                '\n', '') if event_value else 'None'
            events[event_key] = event_value
        return events
    
    def get_hotel_services(self,hotel):
        hotel_services = hotel.css('.hotel-facilities-group')
        services = {}
        for service in hotel_services:
            service_key = service.css(
                '.hotel-facilities-group__title-text::text').getall()[1]
            service_key = service_key.replace(
                '\n', '') if service_key else 'None'
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
                    service_value = service_value.replace(
                        '\n', '') if service_value else 'None'
                    services[service_key].append(service_value)
        return services
    
    def get_hotel_comments(self,hotel):
        hotel_comments = hotel.css(
            '.c-review__body--original::text').getall()
        first_comment = hotel_comments[0] if len(
            hotel_comments) > 0 else 'None'
        second_comment = hotel_comments[1] if len(
            hotel_comments) > 1 else 'None'
        return f'first_comment:{first_comment}. second_comment: {second_comment}'
    
    def get_hotel_images_url(self, hotel):
        image_urls = hotel.css('.active-image img ::attr(src)').getall()
        return image_urls

    
    def push_hotel_data_to_properties(self,hotel):
        self.properties['hotel_name'] = self.get_hotel_name(hotel)
        self.properties['hotel_address'] = self.get_hotel_address(hotel)
        self.properties['hotel_descrption'] = self.get_hotel_description(hotel)
        self.properties['hotel_rate'] = self.get_hotel_rate(hotel)
        self.properties['number_of_stars'] = self.get_hotel_number_of_stars(hotel)
        self.properties['events_near_hotel'] = self.get_hotel_events(hotel)
        self.properties['hotel_services'] = self.get_hotel_services(hotel)
        self.properties['hotel_comments'] = self.get_hotel_comments(hotel)

