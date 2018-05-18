# -*- coding: utf-8 -*-
from myopen.message import Message

__all__ = ['BaseCommand']


class BaseCommand(object):

    def __init__(self, system, params=None):
        self.system = system
        self.log = system.log
        self.msg_handler = None
        self._ended = False
        self.params = params

    @property
    def is_done(self):
        return self._ended

    def start(self):
        self.log('%s does nothing' % self.__class__.__name__)

    def send(self, msg):
        self.system.gateway.send(msg)

    def dispatch(self, pkt):
        self.log('BaseCommand.dispatch %s' % (str(pkt)))
        msg = Message(pkt, self.system)
        msg.parse()
        if self.msg_handler is not None:
            return self.msg_handler(msg)
        return self.default_msg_handler(msg)

    def default_msg_handler(self, msg):
        self.log('BaseCommand.default_msg_handler : %s'
                 % (str(msg)))
        return False

    def end(self):
        self._ended = True
        self.log('BaseCommand.end %s' % (str(self._ended)))
        return True