# -*- coding: utf-8 -*-

from .subsystem import OWNSubSystem
from .lighting import Lighting                         #    1
from .temp_control import TempControl                  #    4
from .gateway import Gateway                           #   13
from .cen_plus_dry_contacts import CenPlusDryContacts  #   25
from .diag_scannable import DiagScannable        
from .diag_lighting import DiagLighting                # 1001
from .diag_temp_control import DiagTempControl         # 1004
from .diag_gateway import DiagGateway                  # 1013


__all__ = [
    'OWNSubSystem',
    'Lighting', 'TempControl', 'Gateway',
    'DiagLighting', 'DiagTempControl', 'DiagGateway',
    'DiagScannable',
    'TX_CMD_SCAN_SYSTEM', 'TX_CMD_DIAG_ABORT',
    'TX_CMD_DIAG_ID', 'TX_CMD_SCAN_CHECK',
    'TX_CMD_RESET', 'TX_CMD_PARAM_ALL_KO',
    'find_subsystem',
    'find_diag_subsystem', 'find_scannable',
    'replace_in_command'
]

SubSystems = [Lighting,
              TempControl,
              Gateway,
              CenPlusDryContacts,
              DiagLighting,
              DiagTempControl,
              DiagGateway, ]

TX_CMD_REQ_GATEWAY_MODEL = "*#13**15##"
TX_CMD_REQ_GATEWAY_FW_VERSION = "*#13**16##"

TX_CMD_SCAN_SYSTEM = "*#[who]*0*13##"
TX_CMD_DIAG_ABORT = "*[who]*6*0##"
TX_CMD_DIAG_ID = "*[who]*10#[id]*0##"
TX_CMD_SCAN_CHECK = "*[who]*11#[id]*0##"
TX_CMD_RESET = "*[who]*12*0##"
TX_CMD_PARAM_ALL_KO = "*#[who]*0*38#0##"


# returns the appropriate class object
def find_subsystem(who):
    for s in SubSystems:
        if isinstance(who, int):
            if getattr(s, 'SYSTEM_WHO', None) == who:
                return s
        if isinstance(who, str):
            if getattr(s, 'SYSTEM_NAME', 'UNKNOWN') == who:
                return s
    return None

def find_diag_subsystem(who):
    for s in SubSystems:
        if getattr(s, 'SYSTEM_DIAG_WHO', None) == who:
            return s
    return None


def find_scannable():
    _scan = []
    for s in SubSystems:
        if getattr(s, 'SYSTEM_IS_SCANNABLE', False):
            _scan.append(s)
    return _scan


def replace_in_command(command, params):
    _cmd = ''
    _in_var = False
    _var = ''
    for c in command:
        if _in_var:
            if c == ']':
                # replace var
                if _var in params.keys():
                    _cmd += str(params[_var])
                _in_var = False
                _var = ''
            else:
                _var += c
            continue
        if c == '[':
            _in_var = True
            continue
        _cmd += c
    return _cmd
