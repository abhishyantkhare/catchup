import secrets

def generate_token():
  return secrets.token_urlsafe(16)

def get_error(msg):
  return {"error": msg}