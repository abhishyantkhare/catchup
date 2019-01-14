import util
from mongoengine import *
from event import Event
from user import User
from stored_event import StoredEvent

class Catchup(Document):
  catchup_title = StringField()
  catchup_owner = EmailField()
  accepted_users = ListField(EmailField())
  invited_users = ListField(EmailField())
  current_event = EmbeddedDocumentField(Event)
  frequency = StringField()
  free_times = ListField(ListField(DateTimeField()))
  central_location = GeoPointField()
  common_radius = IntField()

  def create_catchup(owner, invited_list, title):
    catchup_obj = Catchup(catchup_title = title,
                          catchup_owner = owner,
                          invited_users = invited_list,
                          accepted_users = [],
                          current_event = None,
                          frequency = "Weekly",
                          free_times = [],
                          central_location = None,
                          common_radius = 0
                          ).save()
    util.send_emails(invited_list)
    catchup_obj.save()
    return catchup_obj

  def accept_user(self, user_email):
    if user_email in self.invited_users:
      self.invited_users.remove(user_email)
    if user_email not in self.accepted_users:
      self.accepted_users.append(user_email)
    self.check_and_schedule()
    self.save()

  def deny_user(self, user_email):
    if user_email in self.invited_users:
      self.invited_users.remove(user_email)
    self.check_and_schedule()
    self.save()
  
  def check_and_schedule(self):
    if (self.validate_acceptance()):
      self.generate_new_event()
      # self.schedule_event()
  

  def validate_acceptance(self):
    return not len(self.invited_users)

  def generate_new_event(self):
    busy_times = self.get_busy_times()
    owner_obj = User.objects.get(email=self.catchup_owner)
    time_zone = util.get_user_timezone(owner_obj)
    #Make this generic
    event = StoredEvent.objects.get(event_name="Dinner")
    event_dates = [util.string_to_datetime(date_str, time_zone) for date_str in event.preferred_times]
    start_date, end_date = event.find_free_date(event_dates, busy_times)
    if start_date:
      print(start_date)
      print(end_date)
      self.schedule_event(event, start_date, end_date)


  def get_busy_times(self):
    owner_obj = User.objects.get(email=self.catchup_owner)
    accepted_users_objs = [User.objects.get(email=user_email) for user_email in self.invited_users]
    user_objs = [owner_obj] + accepted_users_objs
    busy_times = []
    for user_obj in user_objs:
      busy_times.extend(util.get_user_busy_time(user_obj))
    busy_times_global = util.merge_busy_times(busy_times)
    return busy_times_global

  def schedule_event(self, stored_event, start_date, end_date):
    event = Event.create_event(stored_event.event_name, start_date.isoformat(), end_date.isoformat(), [-1,-1], stored_event.event_duration)
    attendees = [{'email': self.catchup_owner}] + [{'email': email} for email in self.accepted_users]
    for attendee in attendees:
      user_obj = User.objects.get(email=attendee['email'])
      util.add_event(user_obj, event, attendees)
    self.current_event = event