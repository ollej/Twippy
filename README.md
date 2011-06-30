Twippy
======

A twitter bot with plugin support.

Description
-----------
A generic bot that can connect to a twitter account and react to searches mathcing a specific string.

Uses the same plugin system as Twippy, which means there are a lot of available plugins already.


Main features
-------------
These are the main features of Twippy:

 * Automatic perodical searches for a given text.
 * Multiple plugins can be used for the same account.
 * Ignorelist for users that should be ignored (not quite implemented)
 * Plugins with bot commands can easily be written.
 * Easily configured using command line options or config file.
 * Includes the Gold Quest game as a default plugin.
 * Several plugins available via Shoutbridge: Quotes, Definitions, Dice roller, Name generator, Eliza, Slap etc.


License
-------
Twippy is released under The MIT License. See LICENSE file for more details.


Requirements
------------
 * Python 2.6
 * SQLAlchemy
 * BeautifulSoup
 * Sqlite
 * Tweepy
 * simplejson (for Google plugin)

Installation
------------
Twippy requires a few extra python modules to run.

Install necessary modules:

    $ sudo easy_install Twisted
    $ sudo easy_install sqlalchemy
    $ sudo easy_install tweepy
    $ sudo easy_install beautifulsoup
    $ sudo easy_install simplejson

Next, create a configuration file from the example.

    $ cp config-example.ini config.ini

Edit the config.ini file and change the values to something appropriate.


Running Twippy
--------------
Now you should be ready to start the program:

    $ python twippy.py


Configuration Options
---------------------
There are a lot of available configuration options for Twippy.

 * debug - Print debug information. Raw xml sent/received, sqlalchemy output etc.
 * verbose - Prints information on what the script is doing.
 * quiet - Make script quiet as a mouse, not outputting anything.
 * twitter_consumer_key - Twitter consumer key.
 * twitter_consumer_secret - Twitter consumer secret.
 * twitter_oauth_token - Twitter OAuth token.
 * twitter_oauth_token_secret - Twitter OAuth token secret.
 * twitter_stream = Set to true to use Twitter streaming API for faster response time.
 * twitter_username = Username of account (used by streaming API)
 * twitter_password = Password of account (used by streaming API)
 * twitter_update_time - Seconds between each twitter search.
 * twitter_search - The text to search twitter statuses for.
 * ignorelist - Comma separated list of twitter names to ignore.
 * sender_nick - Add nick of sender to all tweets (based on plugin)
 * plugins - Comma separated list of plugin names to load.

### Twitter Authentication ###
In order to use this script you will have to set it up to authenticate to
a Twitter account.

Twitter uses OAuth for authentication, which means that you will have to
register your own instance of Shoutbridge as an application at
http://dev.twitter.com where you need to log in using the account you want
the application to tweet as.

Under OAuth settings for your application you will find "Consumer key" and
"Consumer secret". Enter these into the config file as the options
twitter_consumer_key and twitter_consumer_secret

Under "My Access Token" you will find the oauth_token and oauth_token_secret
which you will need to place in the options twitter_oauth_token and
twitter_oauth_token_secret

Command Line Options
--------------------
Twippy has a number of command line options available. All configuration
options can be overridden with a corresponding command line option.

Additionally, it is possible to select another configuration file and
section than the default.

There are also three options to change how much information shoutbridge
should output on the terminal: debug, quiet and verbose

Note: Not all of these are implemented yet.

### Options: ###
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    -c FILE, --config=FILE
                          Read configuration from FILE
    -S SECTION, --section=SECTION
                          Read configuration from SECTION
    -D, --debug           Print RAW data sent and received on the stream.
    -q, --quiet           Don't print status messages to stdout
    -v, --verbose         make lots of noise [default]
    -L SECS, --loop=SECS  Search Twitter messages every SECS.
    -X PLUGINS, --plugins=PLUGINS
                          Load comma separated extensions/plugins.
    -n SHOW_NICK, --show-nick=SHOW_NICK
                          Prepend originating nick to each message.
    -F FORMAT, --date-format=FORMAT
                          Use this date format when logging.

Plugins
-------
Twippy has a plugin system to allow new bot commands and general message handling.

Which plugins are loaded is defined by the "plugins" configuration and command line option.

A number of plugins are available by default, and it's very easy to write new ones.

Commands can have synonyms, i.e. multiple commands trigger the same method handler.

See http://github.com/ollej/shoutbridge for a list of available plugins.

The plugin files need to be downloaded from there and placed in the plugins/ folder
and then the name has to be added to the plugins configuration in the config.ini file.


TODO
----
Some ideas for future development.

 * List of twitter searches and which plugin command to match them to.
 * Automatically get oauth token.
 * Import Shoutbridge plugin (and utils/) automatically instead of copies.

