#!/usr/bin/env python3
#
# Copyright (C) 2020-2021 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sys import argv
from sys import exit

from vyos.config import Config
from vyos.template import render_to_string
from vyos import ConfigError
from vyos import frr
from vyos import airbag
airbag.enable()

frr_daemon = 'zebra'

def get_config(config=None):
    if config:
        conf = config
    else:
        conf = Config()

    # This script only works with a passed VRF name
    if len(argv) < 1:
        raise NotImplementedError
    vrf = argv[1]

    # "assemble" dict - easier here then use a full blown get_config_dict()
    # on a single leafNode
    vni = { 'vrf' : vrf }
    tmp = conf.return_value(['vrf', 'name', vrf, 'vni'])
    if tmp: vni.update({ 'vni' : tmp })

    return vni

def verify(vni):
    return None

def generate(vni):
    vni['new_frr_config'] = render_to_string('frr/vrf-vni.frr.tmpl', vni)
    return None

def apply(vni):
    # add configuration to FRR
    frr_cfg = frr.FRRConfig()
    frr_cfg.load_configuration(frr_daemon)
    frr_cfg.modify_section(f'^vrf [a-zA-Z-]*$', '')
    frr_cfg.add_before(r'(interface .*|line vty)', vni['new_frr_config'])
    frr_cfg.commit_configuration(frr_daemon)

    # Save configuration to /run/frr/config/frr.conf
    frr.save_configuration()

    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        exit(1)
