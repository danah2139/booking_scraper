from scrapy.pipelines.images import ImagesPipeline


class customImagePipeline(ImagesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return item.get('hotel_name')+'/' + request.url.split('/')[-1].split('?')[0]
