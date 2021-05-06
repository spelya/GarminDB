"""Class that encapsulates config data for the application."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"


class GarminDBConfig(object):
    """Class that encapsilates config data for the application."""

    db = {
        'type'                  : 'sqlite'
    }

    directories = {
        'relative_to_home'      : True,
        'base_dir'              : 'HealthData',
        'plugins_dir'           : "Plugins",
        'fit_file_dir'          : 'FitFiles',
        'fitbit_file_dir'       : 'FitBitFiles',
        'mshealth_file_dir'     : 'MSHealth',
        'db_dir'                : 'DBs',
        'backup_dir'            : 'Backups',
        'sleep_files_dir'       : 'Sleep',
        'activities_file_dir'   : 'Activities',
        'monitoring_file_dir'   : 'Monitoring',
        'weight_files_dir'      : 'Weight',
        'rhr_files_dir'         : 'RHR'
    }

    config = {
        'metric'                : False
    }

    device_directories = {
        'base'                  : 'garmin',
        'activities'            : 'activity',
        'monitoring'            : 'monitor',
        'sleep'                 : 'sleep',
        'settings'              : 'settings'
    }

    graphs = {
        'size'                  : [12.0, 8.0],
        'steps'                 : {'period' : 'weeks', 'days' : 730},
        'hr'                    : {'period' : 'weeks', 'days' : 730},
        'itime'                 : {'period' : 'weeks', 'days' : 730},
        'weight'                : {'period' : 'weeks', 'days' : 730}
    }

    checkup = {
        'look_back_days'        : 90
    }
