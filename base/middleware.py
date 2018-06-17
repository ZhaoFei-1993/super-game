# -*- coding: UTF-8 -*-
def is_registered(exception):
    try:
        return exception.is_an_error_response
    except AttributeError:
        return False


class RequestExceptionHandler(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @staticmethod
    def process_exception(request, exception):
        if is_registered(exception):
            status = exception.status_code
            exception_dict = exception.to_dict(request)
            return exception_dict


class SetRemoteAddrFromForwardedFor(object):
  def process_request(self, request):
    try:
      real_ip = request.META['HTTP_X_FORWARDED_FOR']
    except KeyError:
      pass
    else:
      # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
      # Take just the first one.
      real_ip = real_ip.split(",")[0]
      request.META['REMOTE_ADDR'] = real_ip