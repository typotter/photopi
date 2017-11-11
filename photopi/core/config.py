"""
Classes and routines for loading configuration for the application.
See :class:`Configuration` for more information.
"""
import logging
import os
import yaml

class ConfigNotFoundError(RuntimeError):
    """ Raised Error when a configuration file cannot be found. """
    pass


_CONFIG_LOCATIONS = ['photopi.yaml', os.path.expanduser('~/.photopi.yaml'),
                     os.path.join('/etc', 'photopi.yaml')]

class Configuration():
    """
    This class represents configuration loaded from a local file or other
    source. By default, config will be loaded from a file found at one of the
    following locations:

    - ./photopi.yaml
    - ~/.phototpi.yaml
    - /etc/photopi.yaml

    The first file found wins. This library simply loads the configuration
    from the file and presents it to the client as a dictionary.

    .. code-block::yaml
        device_name: pp1

    """

    def __init__(self, config_path=None):
        """
        Loads configuration file from the path specified by ``config_path``,
        or if not set, the ones returned by :var:`_CONFIG_LOCATIONS`.
        """
        self.log = logging.getLogger(
            "{}.{}".format(self.__class__.__module__, self.__class__.__name__))
        self._config = self._get_config(config_path)

    def _get_config(self, config_path=None):
        if config_path:
            return self._read_config_file(config_path)
        else:
            for conffile in _CONFIG_LOCATIONS:
                try:
                    return self._read_config_file(conffile)
                except ConfigNotFoundError:
                    pass
        raise ConfigNotFoundError(
            "No configuration files could be found in any of: {}".format(
                ', '.join(_CONFIG_LOCATIONS)))

    @staticmethod
    def _read_config_file(filename):
        "Read a config file and raise a ConfigNotFoundError if not found"
        try:
            with open(filename, 'r') as config:
                return yaml.load(config)
        except IOError:
            raise ConfigNotFoundError(
                "Configuration file {} was not found".format(
                    filename))

    def __str__(self):
        return str(self._config)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self._config, key)
        except KeyError:
            return None
