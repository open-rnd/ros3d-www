#
# Copyright (c) 2015 Open-RnD Sp. z o.o.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Utility classes for Ros3D"""

import logging
import ConfigParser
import os.path
import os

class ConfigLoader(object):
    """Ros3D system configuration loader"""

    DEFAULT_PATH = '/etc/ros3d.conf'
    DEFAULT_REST_URL = 'http://localhost:8090'
    CONFIG_PATH = DEFAULT_PATH

    logger = logging.getLogger(__name__)

    def __init__(self, path=None):
        self.config = None
        self._load_config(path if path else ConfigLoader.CONFIG_PATH)

    def _load_config(self, path):
        """Load configuration from file given by `path`"""
        self.config = ConfigParser.ConfigParser()

        loaded = self.config.read(path)
        if not loaded:
            self.logger.error('failed to load configuration from %s',
                              path)

    def _get(self, section, name, default=None):
        """Try to get an option from configuration. If option is not found,
        return `default`"""
        try:
            return self.config.get(section, name)
        except ConfigParser.Error:
            self.logger.exception('failed to load %s:%s, returning default %r',
                                  section, name, default)
            return default

    def get_system(self):
        """Get assigned system"""
        sys_name = self._get('common', 'system', '')
        return sys_name

    def set_system(self, value):
        if not self.config.has_section('common'):
            self.config.add_section('common')
        if value == None:
            value = ''
        self.config.set('common', 'system', value)

    def get_aladin(self):
        """Get Aladin control mode"""
        return self._get('common', 'aladin', 'READ_ONLY')

    def set_aladin(self, value):
        if not self.config.has_section('common'):
            self.config.add_section('common')
        self.config.set('common', 'aladin', value)

    def get_rest_url(self):
        """Get ROS3D dev controller REST API url"""
        return self._get('rest', 'url', self.DEFAULT_REST_URL)

    def write(self):
        import tempfile
        import shutil

        fd, path = tempfile.mkstemp()
        self.logger.debug('writing config to temp file: %s', path)
        with os.fdopen(fd, 'w') as outf:
            self.config.write(outf)

        self.logger.debug('replacing %s', ConfigLoader.CONFIG_PATH)
        shutil.move(path, ConfigLoader.CONFIG_PATH)

    @classmethod
    def set_config_location(cls, path):
        cls.logger.debug('setting config path to %s', path)
        cls.CONFIG_PATH = path


def get_hostname():
    """Obtain hostname, returns None if hostname is not set"""

    # try environment first
    hostname = os.environ.get('HOSTNAME')

    etc_hostname = '/etc/hostname'
    # bad luck, try /etc/hostname
    if not hostname and os.path.exists(etc_hostname):
        with open(etc_hostname) as inf:
            hostname = inf.read().strip()

    return hostname
