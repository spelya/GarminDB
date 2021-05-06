"""Class that takes a parsed monitoring FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import traceback
import datetime

import Fit
import GarminDB
import utilities
from fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class MonitoringFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed monitoring FIT file object and imports it into a database."""

    def __init__(self, db_params, plugin_manager, ignore_dev_fields=False, debug=0):
        """
        Return a new FitFileProcessor instance.

        Paramters:
        db_params (dict): database access configuration
        ignore_dev_fields (Boolean): If True, then ignore develoepr fields in Fit files
        debug (Boolean): if True, debug logging is enabled
        """
        root_logger.info("Ignore dev fields: %s Debug: %s", ignore_dev_fields, debug)
        super().__init__(db_params, plugin_manager, ignore_dev_fields, debug)
        self.garmin_mon_db = GarminDB.MonitoringDB(db_params, self.debug - 1)

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        with self.garmin_db.managed_session() as self.garmin_db_session, self.garmin_mon_db.managed_session() as self.garmin_mon_db_session:
            self._write_message_types(fit_file, fit_file.message_types)
            # Now write a file's worth of data to the DB
            self.garmin_mon_db_session.commit()
            self.garmin_db_session.commit()

    def _write_monitoring_info_entry(self, fit_file, message_fields):
        activity_types = message_fields.activity_type
        if isinstance(activity_types, list):
            for index, activity_type in enumerate(activity_types):
                entry = {
                    'file_id'                   : GarminDB.File.s_get_id(self.garmin_db_session, fit_file.filename),
                    'timestamp'                 : message_fields.local_timestamp,
                    'activity_type'             : activity_type,
                    'resting_metabolic_rate'    : self._get_field_value(message_fields, 'resting_metabolic_rate'),
                    'cycles_to_distance'        : message_fields.cycles_to_distance[index],
                    'cycles_to_calories'        : message_fields.cycles_to_calories[index]
                }
                GarminDB.MonitoringInfo.s_insert_or_update(self.garmin_mon_db_session, entry)

    def _write_monitoring_entry(self, fit_file, message_fields):
        # Only include not None values so that we match and update only if a table's columns if it has values.
        entry = utilities.list_and_dict.dict_filter_none_values(message_fields)
        timestamp = fit_file.utc_datetime_to_local(message_fields.timestamp)
        # Hack: daily monitoring summaries appear at 00:00:00 localtime for the PREVIOUS day. Subtract a second so they appear int he previous day.
        if timestamp.time() == datetime.time.min:
            timestamp = timestamp - datetime.timedelta(seconds=1)
        entry['timestamp'] = timestamp
        logger.debug("monitoring entry: %r", entry)
        try:
            intersection = GarminDB.MonitoringHeartRate.intersection(entry)
            if len(intersection) > 1 and intersection['heart_rate'] > 0:
                GarminDB.MonitoringHeartRate.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringIntensity.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringIntensity.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.MonitoringClimb.intersection(entry)
            if len(intersection) > 1:
                GarminDB.MonitoringClimb.s_insert_or_update(self.garmin_mon_db_session, intersection)
            intersection = GarminDB.Monitoring.intersection(entry)
            if len(intersection) > 1:
                GarminDB.Monitoring.s_insert_or_update(self.garmin_mon_db_session, intersection)
        except ValueError:
            logger.error("write_monitoring_entry: ValueError for %r: %s", entry, traceback.format_exc())
        except Exception:
            logger.error("Exception on monitoring entry: %r: %s", entry, traceback.format_exc())

    def _write_respiration_entry(self, fit_file, message_fields):
        logger.debug("respiration message: %r", message_fields)
        rr = self._get_field_value(message_fields, 'respiration_rate')
        if rr > 0:
            respiration = {
                'timestamp' : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'rr'        : rr,
            }
            if fit_file.type is Fit.FileType.monitoring_b:
                GarminDB.MonitoringRespirationRate.s_insert_or_update(self.garmin_mon_db_session, respiration)
            else:
                raise(ValueError(f'Unexpected file type {repr(fit_file.type)} for respiration message'))

    def _write_pulse_ox_entry(self, fit_file, message_fields):
        logger.debug("pulse_ox message: %r", message_fields)
        if fit_file.type is Fit.FileType.monitoring_b:
            pulse_ox = self._get_field_value(message_fields, 'pulse_ox')
            if pulse_ox is not None:
                pulse_ox_entry = {
                    'timestamp': fit_file.utc_datetime_to_local(message_fields.timestamp),
                    'pulse_ox': pulse_ox,
                }
                GarminDB.MonitoringPulseOx.s_insert_or_update(self.garmin_mon_db_session, pulse_ox_entry)
        else:
            raise(ValueError(f'Unexpected file type {repr(fit_file.type)} for pulse ox'))
