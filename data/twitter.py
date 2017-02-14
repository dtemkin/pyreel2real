##
##class twitter_data:
##    import tweepy
##    def __init__(self):
##        self.access_token = '4508628568-iBG5EeWTKlUBvrxozrlE4Sr9j0A44LgoVi4Kjnv'
##        self.access_secret = '5fkHmVMuABPvBo7jIAlIjo3jLTFOdwbw5nb12mNtHL9qX'
##        self.consumer_key = 'HerFWGX0qeuXZVHlshJeaeePc'
##        self.consumer_secret = 'DMhNuFfWaq21bFivxpP2XAolQb3SQke1USfOVi3gPuZsEccWZH'
##
##    def get_followers(self, actor_name, actor_num):
##
##        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
##        auth.set_access_token(self.access_token, self.access_secret)
##        api = tweepy.API(auth)
##        try:
##            user = tweepy.api.get_user('%s' % str(actor_name).replace(' ',''))
##        except Exception as err:
##            print("User Not Found")
##            pass
##        else:
##            return {'actor%s_numfollowers' % (actor_num) :user.followers_count}
##            
