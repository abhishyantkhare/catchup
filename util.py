import secrets
from user import User

def generate_token():
  return secrets.token_urlsafe(16)

def get_error(msg):
  return {"error": msg}

def validate_user(user_email, session_token):
  if not User.objects(email=user_email):
    return False, get_error("No Such User")
  user_obj = User.objects.get(email=user_email)
  if user_obj.session_token != session_token:
    return False, get_error("Invalid Session Token")
  return True, user_obj
