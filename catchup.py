import util
from mongoengine import *
from event import Event
from user import User

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
    catchup_obj.save()
    util.send_emails(invited_list)
    return catchup_obj

  def accept_user(self, user_email):
    # if user_email in self.invited_users:
    #   self.invited_users.remove(user_email)
    # if user_email not in self.accepted_users:
    #   self.accepted_users.append(user_email)
    self.check_and_schedule()
    self.save()
  
  def check_and_schedule(self):
    # if (self.validate_acceptance()):
    self.generate_new_event()
      # self.schedule_event()
  

  def validate_acceptance(self):
    return not len(self.invited_users)

  def generate_new_event(self):
    self.get_free_times()

  def get_free_times(self):
    owner_obj = User.objects.get(email=self.catchup_owner)
    accepted_users_objs = [User.objects.get(email=user_email) for user_email in self.invited_users]
    user_objs = [owner_obj] + accepted_users_objs
    busy_times = []
    for user_obj in user_objs:
      busy_times.extend(util.get_user_free_time(user_obj))
    busy_times_global = util.merge_busy_times(busy_times)
    print(busy_times_global)

  def schedule_event(self):
    print('hi')