class UseCase(object):
    request_object = None

    def execute(self, request_object):
        """
        :param request_object:
        :return:
        """
        self.request_object = request_object
        return self.process_request(request_object)

    def process_request(self, request_object):
        raise NotImplementedError("process_request() not implemented by UseCase class")
