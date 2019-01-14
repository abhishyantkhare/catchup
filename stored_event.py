from mongoengine import *
import datetime
import util

class StoredEvent(Document):
  event_name = StringField()
  preferred_times = ListField(StringField())
  yelp_event = BooleanField()
  event_duration = DecimalField()

  def create_stored_event(event_name, preferred_times, yelp_event, event_duration):
    stored_event = StoredEvent(event_name=event_name,
                              preferred_times=preferred_times,
                              yelp_event=yelp_event,
                              event_duration=event_duration
                              ).save()
    return stored_event

  def find_free_date(self, event_dates, busy_dates):
    for event_date in event_dates:
      start_date = event_date[0]
      end_date = start_date + datetime.timedelta(hours=float(self.event_duration))
      while end_date < event_date[1]:
        if not util.date_in_intervals(busy_dates, start_date) and not util.date_in_intervals(busy_dates, end_date):
          return (start_date, end_date)
        start_date = start_date + datetime.timedelta(minutes=30)
        end_date = start_date + datetime.timedelta(hours=float(self.event_duration))
    return None, None
        
  