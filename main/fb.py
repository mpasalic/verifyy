import urllib2

from main.models import *
import main.facebook as fb

def get_name(at):
    if not at: return ""
    g = fb.GraphAPI(access_token = at )
    me = g.get_object('me')
    return me['first_name'] + ' ' + me['last_name']

def put_wall(at, msg):
    if not at: return None
    g = fb.GraphAPI(access_token = at)
    g.put_object("me", "feed",
                message=msg,
               name= 'VerifyY',
               picture= 'http://myfriendfactory.appspot.com/static/images/wall.png',
               link= 'http://www.verifyy.com',
               actions= [
                    {
                       "name": "View Experiment",
                       "link": "http://www.verifyy.com/"
                    }])



def get_token_from_code(code):
    r = urllib2.urlopen("https://graph.facebook.com/oauth/access_token?client_id=205425319498174&redirect_uri=http://localhost:8000/&client_secret=1a5aa67a3a7f8bbe40422a8d01445e82&code=%s" % code).read()
    return r.split('=')[1]

def get_auth_token(request):
    res = FBAuthCode.objects.filter(user=request.user)
    if not res: return None
    code = res[0].code
    return get_token_from_code(code)

def get_cached_token(request):
    authed = not isinstance(request.user,AnonymousUser)
    if not authed: return None
    res = list(FBAuthToken.objects.filter(user=request.user))
    if not res: return None
    return res[-1].token

def get_profile(token):
    g = fb.GraphAPI(access_token = token)
    return g.get_object("me")

def save_code(user, code):
        at = get_token_from_code(code)
        fba = FBAuthCode(code=code, user=user)
        fba.save()
        
