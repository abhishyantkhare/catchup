from mongoengine import *
import util

class User(Document):
  email = EmailField()
  session_token = StringField()
  location = GeoPointField()
  catchups = ListField(UUIDField())

  def create_user(user_email, user_location):
    if not User.objects(email=user_email):
      user_obj = User(email = user_email, 
                      session_token = '',
                      location = user_location,
                      catchups=[]).save()
    return User.objects.get(email=user_email)

  def add_catchup(self, catchup_id):
    self.catchups.append(catchup_id)
    self.save()
        
