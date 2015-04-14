#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import
from ros3dkrui.system.network import network_provider
import tornado.web
import tornado.template
import logging
import os.path

_log = logging.getLogger(__name__)


class SettingsHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def get(self):
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('settings.html')
        system_entries = [
            dict(name='Assigned Rig', value=None, type='input', id='assigned_rig')
        ]

        net = network_provider().list_interfaces()
        wired = net['wired'][0]
        # format IP address assignment method properly
        wired_method = wired['ipv4']['method']
        if wired_method == 'dhcp':
            wired_method = 'DHCP'
        elif wired_method == 'static':
            wired_method = 'Static'

        _log.debug('first wired interface: %s', wired)
        network_entries = {
            'wired': [
                dict(name='IPv4 Address', value=wired['ipv4']['address'],
                     type='input', id='eth_ipv4_address'),
                dict(name='IPv4 Mask', value=wired['ipv4']['netmask'],
                     type='input', id='eth_ipv4_netmask'),
                dict(name='IPv4 Gateway', value=wired['ipv4']['gateway'],
                     type='input', id='eth_ipv4_gateway'),
                dict(name='IPv4 Method', value=wired_method,
                     type='dropdown', id='eth_ipv4_method',
                     options=['DHCP', 'Static'])
            ]
        }
        self.write(tmpl.generate(system_entries=system_entries,
                                 network_entries=network_entries,
                                 configuration_active=True))


    def post(self):
        _log.debug('configuration set: %s' , self.request)
        _log.debug('body: %s', self.request.body)


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def _uptime(self):
        with open('/proc/uptime') as inf:
            secs = float(inf.read().strip().split()[0])

        days, rest = divmod(int(secs), 3600 * 24)
        hours, rest = divmod(rest, 3600)
        minutes, rest = divmod(rest, 60)
        seconds = rest

        uptime = '{}d {}h {}m {}s'.format(days, hours,
                                          minutes, seconds)
        _log.debug('system uptime: %s', str(uptime))
        return str(uptime)

    def _net(self):
        data = network_provider().list_interfaces()
        network_entries = {
            'wired': [],
            'wireless': []
        }
        # we're intersted in wired and wireless interfaces only
        for itype in network_entries.keys():
            if itype not in data:
                _log.debug('interface type %s not in available interfaces',
                           itype)
                continue

            entry = network_entries[itype]
            # expecting only one interface
            if len(data[itype]) > 1:
                _log.error('more than 1 interface of type %s', itype)

            idata = data[itype][0]
            _log.debug('interface data: %s', idata)

            ipv4 = idata.get('ipv4', None)
            # first interface name
            entry.append(dict(name='Interface', value=idata['name']))
            # MAC address comes next
            entry.append(dict(name='MAC Address', value=idata['mac']))
            # interface status
            if idata['online']:
                entry.append(dict(name='State', value='Up'))
            else:
                # may not be online but still usable with local addressing
                if ipv4 and ipv4['address'].startswith('169.254'):
                    entry.append(dict(name='State', value='Up/Local'))
                else:
                    entry.append(dict(name='State', value='Down'))

            # now fill IPv4 status
            if ipv4:
                # address first
                entry.append(dict(name='IPv4 Address', value=ipv4['address']))
                # network mask
                entry.append(dict(name='IPv4 Mask', value=ipv4['netmask']))
                # gateway
                entry.append(dict(name='IPv4 Gateway', value=ipv4.get('gateway', 'Not set')))
                # IP address source, this can be either DHCP, static,
                # or auto link-local. The connman provider returns
                # DHCP when link-local address was configured
                if ipv4['method'] == 'dhcp':
                    method = 'DHCP'
                    # override address source for link local addresses
                    if ipv4['address'].startswith('169.254'):
                        _log.debug('IP %s like link local address', ipv4['address'])
                        method = 'Link Local'
                else:
                    method = 'Static'
                entry.append(dict(name='Address Source', value=method))

        _log.debug('network entries: %s', network_entries)
        return network_entries

    def get(self):
        _log.debug("get: %r", self.request)
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('status.html')

        system_entries= [
            dict(name='Hostname', value='ros3d-kr'),
            dict(name='Assigned Rig', value='None')
        ]
        system_entries.append(dict(name='Uptime', value=self._uptime()))
        network_entries = self._net()

        self.write(tmpl.generate(system_entries=system_entries,
                                 network_entries=network_entries,
                                 system_active=True))


class Application(tornado.web.Application):

    def __init__(self, document_root):

        self.template_root = os.path.join(document_root,
                                          'templates')
        self.static_root = os.path.join(document_root,
                                        'static')
        uris = [
            (r"/settings", SettingsHandler, dict(app=self)),
            (r"/status", MainHandler, dict(app=self)),
            (r"/", MainHandler, dict(app=self)),
        ]

        super(Application, self).__init__(uris,
                                          autoreload=True,
                                          debug=True,
                                          static_path=self.static_root)

        _log.debug('loading templates from: %s', self.template_root)
        _log.debug('static files from: %s', self.static_root)
        # self.loader = tornado.template.Loader(template_root)

    def get_template_loader(self):
        return tornado.template.Loader(self.template_root)
