import util
from mongoengine import *
from event import Event

class Catchup(Document):
  catchup_id = UUIDField()
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
    catchup_obj = Catchup(catchup_id = util.generate_uuid(),
                          catchup_title = title,
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