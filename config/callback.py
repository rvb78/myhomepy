# -*- coding: utf-8 -*-

import os
import sys
import importlib

from core.logger import LOG_INFO
from myopen.subsystems import find_subsystem

from . import callbacks

PLUGINS_DIRS = "plugins/"


class Condition(object):
    _system_str = None
    _order_str = None
    _device = None

    _subsystem_class = None
    _callback_id = None

    def __init__(self, callback):
        self._callback = callback
        self.log = callback.log

    def __str__(self):
        return "<%s (%s,%s)=>\'%s\'>" % (
            self.__class__.__name__,
            self._system_str,
            self._order_str,
            self.map_condition()
        )

    def loads(self, data):
        self.log('Condition.load')
        self._system_str = data.get("system", None)
        self._order_str = data.get("order", None)
        self._device = data.get("device", None)

        ssc = find_subsystem(self._system_str)
        self._subsystem_class = ssc
        self._callback_id = ssc(self._callback.callbacks.system) \
            .map_callback_name(self._order_str)
        if self._callback_id is None:
            self.log("Unable to find callback \'%s\'" % (self._order_str))
            return

    def __to_json__(self):
        cn = {}
        cn['system'] = self._system_str
        cn['order'] = self._order_str
        cn['device'] = self._device
        return cn

    @property
    def device(self):
        return self._device

    def map_condition(self):
        system = self._callback.callbacks.system
        subsys = self._subsystem_class(system)
        return subsys.map_callback(self._callback_id, self._device)


class Action(object):
    AC_BUILT_IN = 1
    AC_PLUGIN = 2

    action_mode = None

    module = None
    method = None

    params = None

    def __init__(self, callback):
        self.callback = callback
        self.log = callback.log

    def __str__(self):
        a = 'Unknown'
        if self.action_mode == self.AC_BUILT_IN:
            a = "BuiltIn(%s, %s)" % (self.method, str(self.params))
        elif self.action_mode == self.AC_PLUGIN:
            a = "Plugin(%s, %s, %s)" % (self.module, self.method, str(self.params))
        return "<%s %s>" % (self.__class__.__name__, a)

    def loads(self, data):
        _built_in = data.get("built-in", None)
        _plugin = data.get("plugin", None)
        if _built_in is not None and isinstance(_built_in, str):
            self.action_mode = self.AC_BUILT_IN
            self.method = _built_in
            if self.module is None:
                self.log('config.Action.loads: no built-in module specified...')
        elif _plugin is not None and isinstance(_plugin, dict):
            self.action_mode = self.AC_PLUGIN
            self.module = _plugin.get("module", None)
            if self.module is None:
                self.log('config.Action.loads: no module specified for plugin...')
            self.method = _plugin.get("method", None)
            if self.method is None:
                self.log('config.Action.loads: no method specified for plugin...')
        self.params = data.get("params", None)

    def __to_json__(self):
        ac = {}
        if self.action_mode == self.AC_BUILT_IN:
            ac['built-in'] = self.method
        elif self.action_mode == self.AC_PLUGIN:
            pl = {}
            pl['module'] = self.module
            pl['method'] = self.method
            ac['plugin'] = pl
        ac['params'] = self.params
        return ac

    def execute(self, system, order, device, data):
        if self.action_mode == self.AC_BUILT_IN:
            self.log('config.Action.execute : action is a built-in', LOG_INFO)
            return self.exec_built_in(system, order, device, data)
        elif self.action_mode == self.AC_PLUGIN:
            self.log('config.Action.execute : action is a plugin', LOG_INFO)
            return self.exec_plugin(system, order, device, data)
        self.log('config.Action.execute : unknown action type', LOG_INFO)
        return None

    def exec_built_in(self, system, order, device, data):
        from myopen.commands import BUILT_IN_COMMANDS
        cmd_class = None
        for c in BUILT_IN_COMMANDS:
            if c.__name__ == self.method:
                self.log("found built-in command %s" % (str(c)))
                cmd_class = c
                break
        if cmd_class is None:
            self.log("command with name %s not found" % (self.method))
            return False
        self.callback.callbacks.system.push_task(cmd_class, params=self.params)
        return True
        

    def exec_plugin(self, system, order, device, data):
        if self.module is None:
            self.log("config.Action._exec_plugin : Module not specified, cancelling callback")
            return None
        if self.method is None:
            self.log("config.Action._exec_plugin : Method not specified, cancelling callback")
            return None
        self.log('config.Action._exec_plugin: plugin appears valid %s %s'
                 % (str(self.module), str(self.method)), LOG_INFO)
        plugins_paths = PLUGINS_DIRS.split(os.pathsep)
        sys.path.extend(plugins_paths)
        self.log('config.Action._exec_plugin : plugins_paths %s' % (str(plugins_paths)), LOG_INFO)
        # find the file
        m = None
        for path in plugins_paths:
            self.log('config.Action._exec_plugin : looking in path %s' % (str(path)), LOG_INFO)
            dir_contents = os.listdir(path)
            self.log('config.Action._exec_plugin : dir_contents %s' % (str(dir_contents)), LOG_INFO)
            for filename in dir_contents:
                name, ext = os.path.splitext(filename)
                if ext.endswith(".py") and (name == self.module):
                    self.log('config.Action._exec_plugin : found module %s' % (filename), LOG_INFO)
                    # muck with the path and filename at this point...
                    module_name = path.replace('/', '.') + name
                    self.log('config.Action._exec_plugin : importing %s' % (module_name), LOG_INFO)
                    # importlib.invalidate_caches()
                    m = importlib.import_module(module_name, globals())
                    self.log('config.Action._exec_plugin : module imported %s' % (str(m)), LOG_INFO)
        if m is None:
            return None
        # find method
        func = getattr(m, self.method, None)
        if func:
            self.log('config.Action._exec_plugin : calling %s %s %s %s %s' %
                     (str(func), str(system), str(self.params),
                      str(device), str(data)), LOG_INFO)
            res = func(system, self.params, device, data)
            self.log('config.Action._exec_plugin : callback plugin returned %s' % (str(res)), LOG_INFO)
            return res
        self.log('Action._exec_plugin : unable to find function %s' % (str(self.method)), LOG_INFO)
        self.log('Action._exec_plugin%s' % (str(dir(m))), LOG_INFO)
        return None


class Callback(object):
    condition = None
    action = None

    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.log = callbacks.log
        if callbacks is None:
            print("in creating Callback, the Callbacks instance was None")

    def __str__(self):
        return "<%s %s %s>" % (self.__class__.__name__, str(self.condition), str(self.action))

    def loads(self, data):
        # callbacks must have 2 sections :
        cond_data = data.get("conditions", None)
        if cond_data is None:
            cond_data = data.get("condition", None)
        if cond_data is not None:
            self.condition = Condition(self)
            self.condition.loads(cond_data)
        action_data = data.get("action", None)
        if action_data is not None:
            self.action = Action(self)
            self.action.loads(action_data)

    def __to_json__(self):
        data = {}
        if self.condition:
            data['condition'] = self.condition
        if self.action:
            data['action'] = self.action
        return data

    def map_callback(self):
        return self.condition.map_condition()

    def execute(self, system, order, device, data):
        if self.action is not None:
            self.log('config.Callback.execute : action is not None, launching', LOG_INFO)
            return self.action.execute(system, order, device, data)
        self.log('config.Callback.execute : self.action is None => return None')
        return None
