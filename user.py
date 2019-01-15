from mongoengine import *
import util

class User(Document):
  email = EmailField()
  session_token = StringField()
  location = GeoPointField()
  catchups = ListField(ObjectIdField())
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
    user_obj.authorization_code = auth_code
    user_obj.refresh_token = refresh_token
    user_obj.access_token = access_token
    if user_location[0] != -1:
      user_obj.location = user_location
    user_obj.save()
    
    return User.objects.get(email=user_email)

  def add_catchup(self, catchup_id):
    if catchup_id not in self.catchups:
      self.catchups.append(catchup_id)
    self.save()

  def remove_catchup(self, catchup_id):
    if catchup_id in self.catchups:
      self.catchups.remove(catchup_id)
    self.save()
        
