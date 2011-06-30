#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2011 Olle Johansson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import sys
import re
import string
import tweepy
import time
from datetime import datetime, date, timedelta
from twisted.internet import task
from twisted.internet import reactor
from optparse import OptionParser

from utils.ObjectFactory import *
from utils.BridgeClass import BridgeClass
from utils.Conf import Conf
from utils.utilities import loadUrl, strip_tags
from utils.HaliDb import *

class Shout(BridgeClass):
    id = None
    userid = 0
    name = None
    text = None
    time = None

    def __init__(self, id=None, userid=None, name=None, text=None, ts=None):
        self.id = int(id)
        self.name = name
        self.text = text
        if ts:
            d = datetime.fromtimestamp(int(ts))
        else:
            d = datetime.fromtimestamp(int(time.time()))
        if date.today() == datetime.date(d):
            self.time = d.strftime('%H:%M')
        else:
            self.time = d.strftime('%Y-%m-%d %H:%M')

class Twippy(BridgeClass):
    #: Conf object with configuration options to use.
    cfg = None
    #: List of references to loadd bot Plugins.
    plugins = dict()
    #: An ObjectFactory instance to use for loading plugins.
    of = None
    #: List of twitter accounts to ignore messages from.
    ignorelist = []

    def __init__(self):
        # Read command line options.
        (options, args) = self.get_options()

        # Read configuration.
        configfile = options.config or 'config.ini'
        configsection = options.section or 'LOCAL'
        self.cfg = Conf(configfile, configsection)
        self.cfg.set_items(vars(options))
        try:
            for s in self.cfg.ignorelist.split(','):
                self.ignorelist.append(s.strip())
        except AttributeError:
            pass

        # Setup database
        try:
            debug = self.cfg.get_bool('debug')
        except AttributeError:
            debug = False
        self.db = HaliDb('sqlite:///extras/twippy.db', debug)

        # Load list of plugins
        if not self.load_plugins(self.cfg.plugins):
            print "No plugins loaded. Quitting."
            sys.exit(1)

        # setup twitter
        self.setup_twitter()

    def get_options(self):
        parser = OptionParser(version="%prog 1.0")
        parser.add_option("-c", "--config", dest="config", default="config.ini",
                        help="Read configuration from FILE", metavar="FILE")
        parser.add_option("-S", "--section", dest="section", default="LOCAL",
                        help="Read configuration from SECTION", metavar="SECTION")
        parser.add_option("-D", "--debug",
                        action="store_true", dest="debug", default=False,
                        help="Print RAW data sent and received on the stream.")
        return parser.parse_args()

    def load_plugins(self, plugs):
        """
        Imports all configured Plugins and adds them to the list of active plugins.
        """
        if not plugs:
            return
        if not self.of:
            self.of = ObjectFactory()
        pluginlist = plugs.split(',')
        for p in pluginlist:
            try:
                plug = self.of.create(p + "Plugin", mod='plugins', inst='Plugin', args=[self])
            except ImportError, ie:
                self.logprint("Couldn't load plugin:", p, ie)
                continue
            plug.setup()
            self.logprint("Loaded plugin:", plug.name, "\n", plug.description)
            self.plugins[p] = plug
        return len(self.plugins)

    def trigger_plugin_event(self, event, obj):
        """
        Triggers given event on all loaded plugins with obj as argument.
        """
        self.logprint('plugin event triggered:', event, obj)
        if not obj or not event:
            return
        for plugin_name, plugin in self.plugins.items():
            try:
                text = obj.text
                nick = obj.name
            except AttributeError:
                text = obj
                nick = ""
            self.logprint("Sending text to plugin:", obj, plugin_name)
            try:
                (cmd, comobj, func) = self.get_plugin_handler(plugin, event, text)
            except AttributeError:
                self.logprint("Attribute Error encountered in plugin:", plugin_name)
                continue
            except UnicodeDecodeError:
                self.logprint("UnicodeDecodeError on text:", text)
                continue
            try:
                if func:
                    self.logprint("Calling plugin:", plugin_name, event, cmd)
                    plugin.sender_nick = nick
                    return func(obj, cmd, comobj)
                else:
                    self.logprint("No function found.", plugin_name, event, cmd)
            except Exception as e:
                self.logprint("Plugin raised exception:", plugin_name, "\n", type(e), e)

    def get_plugin_handler(self, plugin, event, text):
        """
        Based on a given event type and a text message, return the first
        matching command handler in the given plugin.
        """
        text = text.lower()
        for comobj in plugin.commands:
            if event in comobj['onevents']:
                for cmd in comobj['command']:
                    if cmd == '' or text.startswith(cmd.lower()):
                        return cmd, comobj, getattr(plugin, comobj['handler'])
        return None, None, None

    def send_and_shout(self, text, nick=None):
        self.logprint("send_and_shout:", text, nick)
        if nick and self.cfg.get_bool('sender_nick'):
            text = "%s /%s" % (self.shorten_text(text, 140 - len(nick) + 2), nick)
        self.send_tweet(text)

    def setup_twitter(self):
        """
        Setup the Twitter authentication.
        """
        # Setup Twitter connection.
        #self.logprint("consumer key/secret:", self.cfg.get('twitter_consumer_key'), self.cfg.get('twitter_consumer_secret'))
        #self.logprint("ouath token/secret:", self.cfg.get('twitter_oauth_token'), self.cfg.get('twitter_oauth_token_secret'))
        try:
            auth = tweepy.OAuthHandler(self.cfg.get('twitter_consumer_key'), self.cfg.get('twitter_consumer_secret'))
            auth.set_access_token(self.cfg.get('twitter_oauth_token'), self.cfg.get('twitter_oauth_token_secret'))
        except KeyError, ke:
            print "Couldn't find twitter authentication information in config file:", ke
            sys.exit(1)
        self.twit = tweepy.API(auth)

        # Start listening to Twitter mentions.
        utime = float(self.cfg.get('twitter_update_time'))
        self.logprint("Starting reactor with utime:", utime)
        if utime:
            l = task.LoopingCall(self.listen_loop)
            d1 = l.start(utime)
            reactor.run()
        else:
            self.listen_loop()

    def listen_loop(self):
        """
        Searches for tweets matching a configured string.
        """
        searchstr = self.cfg.get('twitter_search');
        self.search_tweets(searchstr, self.handle_tweet)

    def send_tweet(self, text, toname=None):
        """
        Post shout message to Twitter.
        """
        if toname:
            text = self.shorten_text(text, 140 - len(toname) - 3)
            status = u'@%s: %s' % (toname, text)
        else:
            status = self.shorten_text(text, 140)
        self.logprint("Tweeting:", status)
        try:
            self.twit.update_status(status)
        except tweepy.TweepError, te:
            self.logprint('Twitter raised an exception:', te)

    def search_tweets(self, searchstr, cbfn):
        """
        Load mentions from Twitter and send them to cbfn function (usually self.handle_tweet
        """
        latest_id = int(self.db.get_value('twitter_latest_search_id') or 0)
        self.logprint("Searching tweets using keyword:", searchstr, latest_id)
        tweets = self.twit.search(searchstr, since_id=latest_id)
        for tweet in tweets:
            #self.logprint("search result:", self.print_items(tweet.__dict__.items()))
            self.logprint('Found matching tweet:', tweet.from_user, tweet.text, tweet.id)
            if tweet.id > latest_id:
                latest_id = tweet.id
                self.db.set_value('twitter_latest_search_id', latest_id)
            cbfn(tweet)
        self.logprint("Updated latest_id to:", latest_id)

    def handle_tweet(self, tweet):
        self.logprint("Handling tweet:", tweet)
        self.dump(tweet)
        # Skip tweets from own account.
        if tweet.from_user == self.twit.me().screen_name:
            #print "screen_name = my_name", tweet.user.screen_name, my_name
            self.logprint("Tweet was from myself", tweet)
            return

        # Remove search string from text
        s = self.cfg.get('twitter_search')
        p = re.compile(r'\s*' + s + ':?\s*')
        text = re.sub(p, '', tweet.text, re.IGNORECASE)

        # Ugly hack to make GoldQuest work.
        text = '!quest %s' % text
        message = Shout(id=tweet.id, text=text, name=tweet.from_user)
        self.dump(message)

        # Send text to all plugins.

        status = self.trigger_plugin_event('Message', message)

        # If a string was returned, send it directly.
        if status:
            self.send_tweet(status)

    def shorten_text(self, text, length):
        """
        Shorten text to given length.
        """
        if len(text) <= length:
            return text
        return text[:length-1] + u"…"

    def dump(self, o):
        for k, v in o.__dict__.items():
            print k, v


if __name__ == "__main__":
    twippy = Twippy()

