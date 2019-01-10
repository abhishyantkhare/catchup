from mongoengine import *

class Event(EmbeddedDocument):
  event_name = StringField()
  event_desc = StringField()
  event_start_time = DateTimeField()
  event_end_time = DateTimeField()
  event_location = GeoPointField()