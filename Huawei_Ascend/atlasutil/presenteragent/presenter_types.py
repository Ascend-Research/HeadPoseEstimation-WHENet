
STATUS_DISCONNECT = 0
STATUS_CONNECTED = 1
STATUS_OPEN_CH_REQUEST = 2
STATUS_OPENED = 3
STATUS_EXITING = 4
STATUS_EXITTED = 5

CONTENT_TYPE_IMAGE = 0
CONTENT_TYPE_VIDEO = 1

STATUS_OK = 0
STATUS_ERROR = 1

class Point(object):
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y


class ObjectDetectionResult(object):
    def __init__(self, ltx = 0, lty = 0, rbx = 0, rby = 0, text = None):
        self.object_class = 0
        self.confidence = 0
        self.lt = Point(ltx, lty)
        self.rb = Point(rbx, rby)
        self.result_text = text
   
    def IsRectInvalid(self):
        return ((self.lt.x < 0) or \
                (self.lt.y < 0) or \
                (self.rb.x < 0) or \
                (self.rb.y < 0) or \
                (self.lt.x > self.rb.x) or \
                (self.lt.y > self.rb.y))

