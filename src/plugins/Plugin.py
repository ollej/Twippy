#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2010 Olle Johansson

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

import random
import string

from utils.pyanno import raises, abstractMethod, returnType, parameterTypes, deprecatedMethod, \
                          privateMethod, protectedMethod, selfType, ignoreType, callableType

#from bridges.XmppBridge import *
from utils.BridgeClass import *
from utils.utilities import *

class PluginError(Exception):
    """
    Default Plugin exception.
    """

class NamePluginError(PluginError):
    """
    Couldn't parse out name from tex.
    """

class Plugin(BridgeClass):
    """
    Superclass for Shoutbridge plugins.

    All configured plugins will be setup by the Shoutbridge software on
    startup. The C{commands} attribute should contain a list of command
    objects. These will be read by Shoutbridge to determine which
    methods to call on different events.

    >>> p = Plugin([FakeBridge()])
    >>> p.strip_command("!hi there", "!hi")
    'there'
    >>> p.strip_command("!hi there", "!hello")
    '!hi there'
    >>> p.send_message("Hello World!")
    Message: HALiBot Hello World!
    """
    #: Priority of the Plugin. Use this to control order of plugin calling.
    priority = 0
    #: Name of the Plugin
    name = "Plugin"
    #: Author of the Plugin.
    author = "Olle Johansson"
    #: Short description of the Plugin. Shown by !help command.
    description = "Default Shoutbridge plugin interface."
    #: Default nick to use when sending messages from this Plugin.
    nick = 'HALiBot'
    #: Contains a reference to the XmppBridge that has loaded this plugin.
    bridge = None
    #: List of command objects describing commands and respective handler methods.
    commands = []

    def __init__(self, args):
        try:
            self.bridge = args[0]
        except AttributeError:
            self.logprint("No bridge object given.")
            raise PluginError

    def setup(self):
        """
        Setup method which is called once before any triggers methods are called.
        """
        pass

    @protectedMethod
    @parameterTypes( selfType, str, str )
    @returnType( str )
    def prepend_sender(self, text, sep=': '):
        """
        Returns C{text} with name of sender prepended, separated by C{sep}.
        """
        try:
            if self.sender_nick:
                text = "%s%s%s" % (self.sender_nick, sep, text)
        except AttributeError:
            pass
        return text

    @parameterTypes( selfType, str, str )
    @returnType( str )
    def strip_command(self, text, command):
        """
        Returns C{text} with C{command} stripped away from the beginning.
        """
        return text.replace(command, '', 1).strip()

    @parameterTypes( selfType, str, bool )
    def send_message(self, text, prepend=True):
        """
        Send text as message to both Shoutbox and Jabber conference.
        Prepends name of sender to message.
        """
        if prepend:
            text = self.prepend_sender(text.strip())
        self.bridge.send_and_shout(text, self.nick)

    @parameterTypes( selfType, object, str, dict )
    def show_text(self, shout, command=None, comobj=None):
        """
        A command handler that sends a message with a random string from the 
        list in the C{text} element of the command object.
        If the command object has a C{nick} attribute, this will be used
        as the nick when sending the text, otherwise the default plugin
        nick will be used.
        """
        try:
            nick = comobj['nick']
        except KeyError:
            nick = self.nick
        self.bridge.send_and_shout(random.choice(comobj['text']), nick)

    @parameterTypes( selfType, str )
    @returnType( str, str )
    def get_name(self, text):
        """
        Parses out name from start of text.
        If there is a colon in the first 17 chars, everything before it counts as the name,
        as long as the colon isn't directly followed by a right parenthesis.
        Otherwise, the first word is returned as the name.
        The second string returned is the rest of the text.
        """
        colpos = string.find(text, ':')
        #self.logprint('colpos, char at colpos+1', colpos, text[colpos+1:colpos+2])
        if colpos >= 0 and colpos <= 16 and text[colpos+1:colpos+2] != ')':
            (name, message) = text.split(':', 1)
        else:
            try:
                (name, message) = text.split(' ', 1)
            except ValueError:
                name = text
                message = ""
        return name.strip(), message.strip()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
