from mongoengine import *

class Event(EmbeddedDocument):
  event_name = StringField()
  event_start_time = DateTimeField()
  event_end_time = DateTimeField()
  event_location = GeoPointField()
  event_duration = DecimalField()
  def create_event(event_name, event_start_time, event_end_time, event_location, event_duration):
    event = Event(event_name=event_name,
                  event_start_time=event_start_time,
                  event_end_time=event_end_time,
                  event_location=event_location,
                  event_duration=event_duration
                )
    return event