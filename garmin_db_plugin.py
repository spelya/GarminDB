"""Base classes for plugins."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging

import GarminDB
import utilities


logger = logging.getLogger(__file__)


class GarminDbPluginManager(utilities.PluginManager):
    """Loads python file based plugins that extend GarminDb."""

    def __init__(self, plugin_dir, db_params):
        """Load python file based plugins from plugin_dir."""
        logger.info("Loading GarminDb plugins from %s", plugin_dir)
        super().__init__(plugin_dir, {'db_params': db_params})

    def get_activity_file_processors(self, fit_file):
        """Return a dict of all plugins that handle FIT file messages."""
        result = {}
        for plugin_name, plugin in self.plugins.items():
            if plugin.matches_activity_file(fit_file):
                logger.info("Plugin %s matches file %s", plugin_name, fit_file)
                plugin.init_activity(GarminDB.ActivitiesDB, GarminDB.Activities)
                result[plugin_name] = plugin
        return result
