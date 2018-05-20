# -*- coding: utf-8 -*-
from core.logger import SYSTEM_LOGGER

from .subsystem import OWNSubSystem


class DiagScannable(OWNSubSystem):
    SYSTEM_IS_SCANNABLE = True

    # scan ops
    OP_SCAN_CMD_DIAG_ID = 0
    # config ops

    SCAN_CALLBACKS = {
        'SCAN_CMD_DIAG_ID': OP_SCAN_CMD_DIAG_ID,
    }

    SCAN_REGEXPS = {
        'COMMAND': [
            # system is busy
            (r'^\*3\*0##$', '_diag_busy', ),

            # res_trans_end
            # end of transmission from device
            # *[who]*4*[_junk]##
            {
                'name': 'RES_TRANS_END',
                're': r'^\*4\*(?P<_junk>.*)##$',
                'func': '_diag_res_trans_end'
            },

            # cmd_diag_abort
            # programmer abort diagnostic
            # *[who]*6*0##
            (r'^\*6\*0##$', '_diag_cmd_diag_abort', ),

            # cmd_diag_id
            # programmer starts a diagnostic session wth ID
            # *[who]*10#[id]*0##
            (r'^\*10#(?P<hw_addr>\d{1,10})\*0##$', '_diag_cmd_diag_id', ),

            # cmd_scan_check
            (r'^\*11#(?P<hw_addr>\d{1,10})\*0##$', '_cmd_scan_check', ),

            # scanning subsystem reset
            (r'^\*12\*0##$', '_subsystem_scan_reset', ),

        ],
        'STATUS': [
            # res_object_model
            # device answers with it's object model and number of physical
            # configurators
            # *#[who]*[where]*1*[object_model]*[n_conf]*[brand]*[line]##
            (r'^\*(?P<virt_id>\d{1,4})\*1\*(?P<model_id>\d{1,3})\*'
             r'(?P<nb_conf>\d{1,2})\*(?P<brand_id>\d)\*(?P<prod_line>\d)##$',
             '_diag_res_object_model', ),

            # res_fw_version
            # device answers with it's firmware version
            # *#[who]*[where]*2*[fw_version]##
            (r'^\*(?P<virt_id>\d{1,4})\*2\*(?P<fw_version>.*)##$',
             '_diag_res_fw_version', ),

            # res_conf_1_6
            # device answers with hardware configurators 1 through 6
            # *#[who]*[where]*4*[c1]*[c2]*[c3]*[c4]*[c5]*[c6]##
            (r'^\*(?P<virt_id>\d{1,4})\*4\*(?P<c1>\d{1,3})\*(?P<c2>\d{1,3})\*'
             r'(?P<c3>\d{1,3})\*(?P<c4>\d{1,3})\*(?P<c5>\d{1,3})\*'
             r'(?P<c6>\d{1,3})##$', '_diag_res_conf_1_6', ),

            # res_diag_a
            # device answers with diagnostic bit set A
            # *#[who]*[where]*7*[bitmask_dia_a]##
            (r'^\*(?P<virt_id>\d{1,4})\*7\*(?P<diag_bits>[01]{24})##$',
             '_diag_res_diag_a', ),

            # device diagnostics
            # see notes.txt
            (r'^\*(?P<virt_id>\d{1,4})\*11\*(?P<diag_bits>[01]{24})##$',
             '_analyze_diagnostics', ),

            # res_id
            # device answers with it's ID
            # *#[who]*[where]*13*[id]##
            {
                'name': 'DIAG_RES_ID',
                're': r'^\*(?P<virt_id>\d{1,4})\*13\*(?P<hw_addr>\d{1,10})##$',
                'func': '_diag_res_id'
            },
            # res_ko_value
            # device answers with it's key/object, value and state
            # *#[who]*[where]*30*[slot]*[keyo]*[state]##
            {
                'name': 'RES_KO_VALUE',
                're': r'^\*(?P<virt_id>\d{1,4})\*30\*(?P<slot>\d{1,3})\*'
                      r'(?P<keyo>\d{1,5})\*(?P<state>[01])##$',
                'func': '_diag_res_ko_value'
            },

            # res_ko_sys
            # device answers with it's key/object, system and address",
            # *#[who]*[where]*32#[slot]*[sys]*[addr]##
            (r'^\*(?P<virt_id>\d{1,4})\*32#(?P<slot>\d{1,3})\*(?P<sys>\d{1,3})'
             r'\*(?P<addr>\d{1,5})##$', '_diag_res_ko_sys', ),

            # device answers with the key/value of key/object
            # *#[who]*[where]*35#[index]#[slot]*[val_par]##
            {
                'name': 'RES_PARAM_KO',
                're': r'\*(?P<virt_id>\d{1,4})\*35#(?P<index>\d{1,3})#'
                      r'(?P<slot>\d{1,3})\*(?P<val_par>\d{1,5})##',
                'func': '_diag_res_param_ko'
            },
        ]
    }

    # ---------------------------------------------------------------------
    #
    # Message parsing stuff
    #

    def parse_regexp(self, msg):
        sys_regexps = self.get_regexps(msg, 'SYSTEM_REGEXPS')
        scan_regexps = self.get_regexps(msg, 'SCAN_REGEXPS')
        regexps = sys_regexps + scan_regexps
        return self._parse_regexp(msg, regexps)

    # ---------------------------------------------------------------------
    #
    # Callback stuff
    #

    def map_callback_name(self, name):
        SYSTEM_LOGGER.log('DiagScannable.map_callback_name')
        scan_callbacks = getattr(self, 'SCAN_CALLBACKS', None)
        sys_callbacks = getattr(self, 'SYSTEM_CALLBACKS', None)
        _cb = scan_callbacks.copy()
        SYSTEM_LOGGER.log(_cb)
        if sys_callbacks is not None:
            _cb.update(sys_callbacks)
        _cb_name = self.__class__._map_callback_name(name, _cb)
        SYSTEM_LOGGER.log(_cb_name)
        return _cb_name

    def map_device(self, device):
        self.log('DiagScannable.map_device : %s' % (str(device)))
        if device is None:
            return '*'
        return str(device)

    # ---------------------------------------------------------------------
    #
    # SubSystem-specific functions
    #

    def _diag_busy(self, matches):
        return True

    def _diag_res_trans_end(self, matches):

        def end_of_transmission_event():
            res = self.system.devices.eot_event(self, matches)
            if not res:
                self.log('res_trans_end %s' % (str(matches)))
                return False
            return True

        return end_of_transmission_event

    def _diag_cmd_diag_abort(self, matches):

        def end_of_configuration():
            self.log('Signaling the end of configuration')
            self.system.devices.end_config_read()
            self.system.devices.reset_active_device()
            return True

        return end_of_configuration

    def _diag_cmd_diag_id(self, matches):
        _hw_addr = int(matches.get('hw_addr', None))
        # do the system thing
        res = self.system.devices.set_active_device(self, _hw_addr)
        if not res:
            self.log('DiagScannable._diag_cmd_diad_id ERROR : %s' %
                     (str(matches)))
        # callback
        _order = self.OP_SCAN_CMD_DIAG_ID
        _device = None
        _data = {'hw_addr': _hw_addr}
        return self.gen_callback_dict(_order, _device, _data)

    def _cmd_scan_check(self, matches):
        return True

    def _subsystem_scan_reset(self, matches):
        # self.log('scan reset for %d subsystem' % self.SYSTEM_WHO)
        return True

    def _diag_res_object_model(self, matches):
        _virt_id = matches['virt_id']
        _model_id = int(matches['model_id'])
        _nb_conf = int(matches['nb_conf'])
        _brand_id = int(matches['brand_id'])
        _prod_line = int(matches['prod_line'])
        res = self.system.devices.res_object_model(_virt_id, _model_id,
                                                   _nb_conf, _brand_id,
                                                   _prod_line)
        if not res:
            self.log('DiagScannable._diag_res_object_model ERROR : %s' %
                     (str(matches)))
        return res

    def parse_version(self, version):
        if version[-1] != '*':
            version += '*'
        names = ('major', 'minor', 'build')
        ver = {}
        var = ''
        cur = 0
        for c in version:
            if c.isdecimal():
                var += c
            elif c == '*':
                if cur < len(names):
                    k = names[cur]
                else:
                    k = cur
                ver[k] = int(var)
                var = ''
                cur += 1
        return ver

    def _diag_res_fw_version(self, matches):
        _virt_id = matches['virt_id']
        _fw_ver = self.parse_version(matches['fw_version'])
        res = self.system.devices.res_fw_version(_virt_id, _fw_ver)
        if not res:
            self.log('res_fw_version %s' % (str(matches)))
        return res

    def _diag_res_conf_1_6(self, matches):
        _virt_id = matches['virt_id']
        _c1 = int(matches['c1'])
        _c2 = int(matches['c2'])
        _c3 = int(matches['c3'])
        _c4 = int(matches['c4'])
        _c5 = int(matches['c5'])
        _c6 = int(matches['c6'])
        _c_1_6 = (_c1, _c2, _c3, _c4, _c5, _c6, )
        res = self.system.devices.res_conf_1_6(_virt_id, _c_1_6)
        if not res:
            self.log('res_conf_1_6 %s' % (str(matches)))
        return res

    def _diag_res_diag_a(self, matches):
        self.log('res_diag_a %s' % (str(matches)))
        return True

    def _analyze_diagnostics(self, matches):
        self.log('DiagScannable dev diags : %s' % str(matches))
        return True

    def _diag_res_id(self, matches):
        # self.log('res_id %s' % str(matches))
        _virt_id = matches['virt_id']
        _hw_addr = matches['hw_addr']
        hw_addr_x = self.system.devices.format_hw_addr(_hw_addr)

        def register():
            dev = self.system.devices.register(self, matches)
            if dev is None:
                self.log('Unable to register device with virt_id %s '
                         'and hw_addr %s' % (_virt_id, hw_addr_x))
                return False
            return True

        return register

    def _diag_res_ko_value(self, matches):
        _virt_id = matches['virt_id']
        _slot = int(matches['slot'])
        _keyo = int(matches['keyo'])
        _state = int(matches['state'])
        res = self.system.devices.res_ko_value(_virt_id, _slot, _keyo, _state)
        if not res:
            self.log('res_ko_value %s' % (str(matches)))
        return res

    def _diag_res_ko_sys(self, matches):
        _virt_id = matches['virt_id']
        _slot = int(matches['slot'])
        _sys = int(matches['sys'])
        _addr = int(matches['addr'])
        res = self.system.devices.res_ko_sys(_virt_id, _slot, _sys, _addr)
        if not res:
            self.log('res_ko_sys %s' % (str(matches)))
        return res

    def _diag_res_param_ko(self, matches):
        _virt_id = matches['virt_id']
        _slot = int(matches['slot'])
        _index = int(matches['index'])
        _val_par = int(matches['val_par'])

        def res_param_ko():
            res = self.system.devices.res_param_ko(
                _virt_id, _slot,
                _index, _val_par)
            if not res:
                self.log('failed _diag_res_param_ko.res_param_ko '
                         '%s' % (str(matches)))
            return res

        return res_param_ko
