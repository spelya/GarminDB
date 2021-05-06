"""Test garmin db."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import unittest
import logging
import datetime

from test_db_base import TestDBBase
import Fit
import GarminDB
from garmin_db_config_manager import GarminDBConfigManager


root_logger = logging.getLogger()
handler = logging.FileHandler('garmin_db.log', 'w')
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


class TestGarminDb(TestDBBase, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_params = GarminDBConfigManager.get_db_params()
        cls.garmin_db = GarminDB.GarminDB(db_params)
        table_dict = {
            'attributes_table' : GarminDB.Attributes,
            'device_table' : GarminDB.Device,
            'device_info_table' : GarminDB.DeviceInfo,
            'file_table' : GarminDB.File,
            'weight_table' : GarminDB.Weight,
            'stress_table' : GarminDB.Stress,
            'sleep_table' : GarminDB.Sleep,
            'sleep_events_table' : GarminDB.SleepEvents,
            'resting_heart_rate_table' : GarminDB.RestingHeartRate
        }
        super().setUpClass(cls.garmin_db, table_dict)

    def check_col_stat(self, value_name, value, bounds):
        min_value, max_value = bounds
        self.assertGreaterEqual(value, min_value, '%s value %s less than min %s' % (value_name, value, min_value))
        self.assertLessEqual(value, max_value, '%s value %s greater than max %s' % (value_name, value, max_value))
        logger.info("%s: %s", value_name, value)

    def check_col_stats(self, db, table, col, col_name, ignore_le_zero, time_col,
                        records_bounds, max_bounds, min_bounds, avg_bounds, latest_bounds):
        self.check_col_stat(col_name + ' records', table.row_count(db), records_bounds)
        if time_col:
            maximum = table.get_time_col_max(db, col)
        else:
            maximum = table.get_col_max(db, col)
        self.check_col_stat(col_name + ' max', maximum, max_bounds)
        if time_col:
            minimum = table.get_time_col_min(db, col, None, None)
        else:
            minimum = table.get_col_min(db, col, None, None, ignore_le_zero)
        self.check_col_stat(col_name + ' min', minimum, min_bounds)
        if time_col:
            average = table.get_time_col_avg(db, col, None, None)
        else:
            average = table.get_col_avg(db, col, None, None, ignore_le_zero)
        self.check_col_stat(col_name + ' avg', average, avg_bounds)
        latest = table.get_time_col_latest(db, col) if time_col else table.get_col_latest(db, col, ignore_le_zero)
        self.check_col_stat(col_name + ' latest', latest, latest_bounds)

    def test_garmindb_tables_bounds(self):
        self.check_col_stats(
            self.garmin_db, GarminDB.Weight, GarminDB.Weight.weight, 'Weight', False, False,
            (0, 10*365),
            (25, 300),
            (25, 300),
            (25, 300),
            (25, 300)
        )
        stress_min = -2
        stress_max = 100
        self.check_col_stats(
            self.garmin_db, GarminDB.Stress, GarminDB.Stress.stress, 'Stress', True, False,
            (1, 10000000),
            (25, 100),
            (stress_min, 2),
            (stress_min, stress_max),
            (stress_min, stress_max)
        )
        self.check_col_stats(
            self.garmin_db, GarminDB.RestingHeartRate, GarminDB.RestingHeartRate.resting_heart_rate, 'RHR', True, False,
            (1, 10000000),
            (30, 100),
            (30, 100),
            (30, 100),
            (30, 100)
        )
        self.check_col_stats(
            self.garmin_db, GarminDB.Sleep, GarminDB.Sleep.total_sleep, 'Sleep', True, True,
            (1, 10000000),
            (datetime.time(8), datetime.time(12)),
            (datetime.time(0), datetime.time(4)),
            (datetime.time(4), datetime.time(10)),
            (datetime.time(2), datetime.time(12))
        )
        self.check_col_stats(
            self.garmin_db, GarminDB.Sleep, GarminDB.Sleep.rem_sleep, 'REM Sleep', True, True,
            (1, 10000000),
            (datetime.time(2), datetime.time(8)),           # max
            (datetime.time(0), datetime.time(2)),           # min
            (datetime.time(minute=30), datetime.time(6)),   # avg
            (datetime.time(minute=10), datetime.time(6))    # latest
        )

    def test_measurement_system(self):
        measurement_system = GarminDB.Attributes.measurements_type(self.garmin_db, Fit.field_enums.DisplayMeasure.metric)
        self.assertIn(measurement_system, Fit.field_enums.DisplayMeasure)


if __name__ == '__main__':
    unittest.main(verbosity=2)
