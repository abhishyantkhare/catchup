from mongoengine import *
import util

class User(Document):
  email = EmailField()
  session_token = StringField()
  location = GeoPointField()
  catchups = ListField(UUIDField())
  authorization_code = StringField()
  access_token = StringField()
  refresh_token = StringField()

  def create_user(user_email, user_location, auth_code, refresh_token, access_token):
    if not User.objects(email=user_email):
      user_obj = User(email = user_email, 
                      session_token = '',
                      authorization_code=auth_code,
                      location = user_location,
                      catchups=[]).save()
    user_obj = User.objects.get(email=user_email)
    user_obj.refresh_token = refresh_token
    user_obj.access_token = access_token
    user_obj.save()
    
    return User.objects.get(email=user_email)

  def add_catchup(self, catchup_id):
    self.catchups.append(catchup_id)
    self.save()
        
