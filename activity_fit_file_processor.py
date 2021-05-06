"""Class that takes a parsed activity FIT file object and imports it into a database."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys

import Fit
import GarminDB
from fit_file_processor import FitFileProcessor


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class ActivityFitFileProcessor(FitFileProcessor):
    """Class that takes a parsed activity FIT file object and imports it into a database."""

    def write_file(self, fit_file):
        """Given a Fit File object, write all of its messages to the DB."""
        self.activity_file_plugins = [plugin for plugin in self.plugin_manager.get_activity_file_processors(fit_file).values()]
        if len(self.activity_file_plugins):
            root_logger.info("Loaded %d activity plugins %r for file %s", len(self.activity_file_plugins), self.activity_file_plugins, fit_file)
        # Create the db after setting up the plugins so that plugin tables are handled properly
        self.garmin_act_db = GarminDB.ActivitiesDB(self.db_params, self.debug - 1)
        with self.garmin_db.managed_session() as self.garmin_db_session, self.garmin_act_db.managed_session() as self.garmin_act_db_session:
            self._write_message_types(fit_file, fit_file.message_types)
            # Now write a file's worth of data to the DB
            self.garmin_act_db_session.commit()
            self.garmin_db_session.commit()

    def _plugin_dispatch(self, handler_name, *args, **kwargs):
        result = {}
        for plugin in self.activity_file_plugins:
            function = getattr(plugin, handler_name, None)
            if function:
                result.update(function(*args, **kwargs))
        return result

    def _write_lap(self, fit_file, message_type, messages):
        """Write all lap messages to the database."""
        for lap_num, message in enumerate(messages):
            self._write_lap_entry(fit_file, message.fields, lap_num)

    def _write_record(self, fit_file, message_type, messages):
        """Write all record messages to the database."""
        for record_num, message in enumerate(messages):
            self._write_record_entry(fit_file, message.fields, record_num)

    def _write_record_entry(self, fit_file, message_fields, record_num):
        # We don't get record data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write the new data out if it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        plugin_record = self._plugin_dispatch('write_record_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields, record_num)
        if not GarminDB.ActivityRecords.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'record' : record_num}):
            record = {
                'activity_id'                       : activity_id,
                'record'                            : record_num,
                'timestamp'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'position_lat'                      : self._get_field_value(message_fields, 'position_lat'),
                'position_long'                     : self._get_field_value(message_fields, 'position_long'),
                'distance'                          : self._get_field_value(message_fields, 'distance'),
                'cadence'                           : self._get_field_value(message_fields, 'cadence'),
                'hr'                                : self._get_field_value(message_fields, 'heart_rate'),
                'rr'                                : self._get_field_value(message_fields, 'respiration_rate'),
                'altitude'                          : self._get_field_value(message_fields, 'altitude'),
                'speed'                             : self._get_field_value(message_fields, 'speed'),
                'temperature'                       : self._get_field_value(message_fields, 'temperature'),
            }
            record.update(plugin_record)
            root_logger.info("_write_record_entry activity_id %s, record %s doesn't exist", activity_id, record_num)
            self.garmin_act_db_session.add(GarminDB.ActivityRecords(**record))

    def _write_lap_entry(self, fit_file, message_fields, lap_num):
        # we don't get laps data from multiple sources so we don't need to coellesce data in the DB.
        # It's fastest to just write new data out if the it doesn't currently exist.
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        plugin_lap = self._plugin_dispatch('write_lap_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields, lap_num)
        if not GarminDB.ActivityLaps.s_exists(self.garmin_act_db_session, {'activity_id' : activity_id, 'lap' : lap_num}):
            lap = {
                'activity_id'                       : GarminDB.File.id_from_path(fit_file.filename),
                'lap'                               : lap_num,
                'start_time'                        : fit_file.utc_datetime_to_local(message_fields.start_time),
                'stop_time'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
                'elapsed_time'                      : self._get_field_value(message_fields, 'total_elapsed_time'),
                'moving_time'                       : self._get_field_value(message_fields, 'total_timer_time'),
                'start_lat'                         : self._get_field_value(message_fields, 'start_position_lat'),
                'start_long'                        : self._get_field_value(message_fields, 'start_position_long'),
                'stop_lat'                          : self._get_field_value(message_fields, 'end_position_lat'),
                'stop_long'                         : self._get_field_value(message_fields, 'end_position_long'),
                'distance'                          : self._get_field_value(message_fields, 'total_distance'),
                'cycles'                            : self._get_field_value(message_fields, 'total_cycles'),
                'avg_hr'                            : self._get_field_value(message_fields, 'avg_heart_rate'),
                'max_hr'                            : self._get_field_value(message_fields, 'max_heart_rate'),
                'avg_rr'                            : self._get_field_value(message_fields, 'avg_respiration_rate'),
                'max_rr'                            : self._get_field_value(message_fields, 'max_respiration_rate'),
                'calories'                          : self._get_field_value(message_fields, 'total_calories'),
                'avg_cadence'                       : self._get_field_value(message_fields, 'avg_cadence'),
                'max_cadence'                       : self._get_field_value(message_fields, 'max_cadence'),
                'avg_speed'                         : self._get_field_value(message_fields, 'avg_speed'),
                'max_speed'                         : self._get_field_value(message_fields, 'max_speed'),
                'ascent'                            : self._get_field_value(message_fields, 'total_ascent'),
                'descent'                           : self._get_field_value(message_fields, 'total_descent'),
                'max_temperature'                   : self._get_field_value(message_fields, 'max_temperature'),
                'avg_temperature'                   : self._get_field_value(message_fields, 'avg_temperature'),
            }
            lap.update(plugin_lap)
            self.garmin_act_db_session.add(GarminDB.ActivityLaps(**lap))

    def _write_steps_entry(self, fit_file, activity_id, sub_sport, message_fields):
        steps = {
            'activity_id'                       : activity_id,
            'steps'                             : self._get_field_value(message_fields, 'total_steps'),
            'avg_pace'                          : Fit.conversions.perhour_speed_to_pace(message_fields.avg_speed),
            'max_pace'                          : Fit.conversions.perhour_speed_to_pace(message_fields.max_speed),
            'avg_steps_per_min'                 : self._get_field_value(message_fields, 'avg_steps_per_min'),
            'max_steps_per_min'                 : self._get_field_value(message_fields, 'max_steps_per_min'),
            'avg_step_length'                   : self._get_field_value(message_fields, 'avg_step_length'),
            'avg_vertical_ratio'                : self._get_field_value(message_fields, 'avg_vertical_ratio'),
            'avg_vertical_oscillation'          : self._get_field_value(message_fields, 'avg_vertical_oscillation'),
            'avg_gct_balance'                   : self._get_field_value(message_fields, 'avg_stance_time_balance'),
            'avg_ground_contact_time'           : self._get_field_value(message_fields, 'avg_stance_time'),
            'avg_stance_time_percent'           : self._get_field_value(message_fields, 'avg_stance_time_percent'),
        }
        steps.update(self._plugin_dispatch('write_steps_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        root_logger.debug("_write_steps_entry: %r", steps)
        GarminDB.StepsActivities.s_insert_or_update(self.garmin_act_db_session, steps, ignore_none=True, ignore_zero=True)

    def _write_running_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_walking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_hiking_entry(self, fit_file, activity_id, sub_sport, message_fields):
        return self._write_steps_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_cycling_entry(self, fit_file, activity_id, sub_sport, message_fields):
        ride = {
            'activity_id'   : activity_id,
            'strokes'       : self._get_field_value(message_fields, 'total_strokes'),
        }
        ride.update(self._plugin_dispatch('write_cycle_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        GarminDB.CycleActivities.s_insert_or_update(self.garmin_act_db_session, ride, ignore_none=True, ignore_zero=True)

    def _write_stand_up_paddleboarding_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("sup sport entry: %r", message_fields)
        paddle = {
            'activity_id'           : activity_id,
            'strokes'               : self._get_field_value(message_fields, 'total_strokes'),
            'avg_stroke_distance'   : self._get_field_value(message_fields, 'avg_stroke_distance'),
        }
        paddle.update(self._plugin_dispatch('write_paddle_entry', self.garmin_act_db_session, fit_file, activity_id, sub_sport, message_fields))
        GarminDB.PaddleActivities.s_insert_or_update(self.garmin_act_db_session, paddle, ignore_none=True, ignore_zero=True)

    def _write_rowing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("row sport entry: %r", message_fields)
        return self._write_stand_up_paddleboarding_entry(fit_file, activity_id, sub_sport, message_fields)

    def _write_boating_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("boating sport entry: %r", message_fields)

    def _write_fitness_equipment_entry(self, fit_file, activity_id, sub_sport, message_fields):
        try:
            function = getattr(self, '_write_' + sub_sport.name + '_entry')
            function(fit_file, activity_id, sub_sport, message_fields)
        except AttributeError:
            root_logger.info("No sub sport handler type %s from %s: %s", sub_sport, fit_file.filename, message_fields)

    def _write_alpine_skiing_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Skiing sport entry: %r", message_fields)

    def _write_swimming_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Swimming sport entry: %r", message_fields)

    def _write_training_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Training sport entry: %r", message_fields)

    def _write_transition_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Transition sport entry: %r", message_fields)

    def _write_generic_entry(self, fit_file, activity_id, sub_sport, message_fields):
        root_logger.debug("Generic sport entry: %r", message_fields)

    def __choose_sport(self, current_sport, current_sub_sport, new_sport, new_sub_sport):
        sport = Fit.Sport.strict_from_string(current_sport)
        sub_sport = Fit.SubSport.strict_from_string(current_sub_sport)
        if new_sport is not None and (sport is None or (not sport.preferred() and new_sport.preferred())):
            sport = new_sport
        if new_sub_sport is not None and (sub_sport is None or (not sub_sport.preferred() and new_sub_sport.preferred())):
            sub_sport = new_sub_sport
        return {'sport' : Fit.field_enums.name_for_enum(sport), 'sub_sport' : Fit.field_enums.name_for_enum(sub_sport)}

    def _write_session_entry(self, fit_file, message_fields):
        activity_id = GarminDB.File.id_from_path(fit_file.filename)
        sport = message_fields.sport
        sub_sport = message_fields.sub_sport
        activity = {
            'activity_id'                       : activity_id,
            'start_time'                        : fit_file.utc_datetime_to_local(message_fields.start_time),
            'stop_time'                         : fit_file.utc_datetime_to_local(message_fields.timestamp),
            'elapsed_time'                      : message_fields.total_elapsed_time,
            'moving_time'                       : self._get_field_value(message_fields, 'total_timer_time'),
            'start_lat'                         : self._get_field_value(message_fields, 'start_position_lat'),
            'start_long'                        : self._get_field_value(message_fields, 'start_position_long'),
            'stop_lat'                          : self._get_field_value(message_fields, 'end_position_lat'),
            'stop_long'                         : self._get_field_value(message_fields, 'end_position_long'),
            'distance'                          : self._get_field_value(message_fields, 'total_distance'),
            'cycles'                            : self._get_field_value(message_fields, 'total_cycles'),
            'laps'                              : self._get_field_value(message_fields, 'num_laps'),
            'avg_hr'                            : self._get_field_value(message_fields, 'avg_heart_rate'),
            'max_hr'                            : self._get_field_value(message_fields, 'max_heart_rate'),
            'avg_rr'                            : self._get_field_value(message_fields, 'avg_respiration_rate'),
            'max_rr'                            : self._get_field_value(message_fields, 'max_respiration_rate'),
            'calories'                          : self._get_field_value(message_fields, 'total_calories'),
            'avg_cadence'                       : self._get_field_value(message_fields, 'avg_cadence'),
            'max_cadence'                       : self._get_field_value(message_fields, 'max_cadence'),
            'avg_speed'                         : self._get_field_value(message_fields, 'avg_speed'),
            'max_speed'                         : self._get_field_value(message_fields, 'max_speed'),
            'ascent'                            : self._get_field_value(message_fields, 'total_ascent'),
            'descent'                           : self._get_field_value(message_fields, 'total_descent'),
            'max_temperature'                   : self._get_field_value(message_fields, 'max_temperature'),
            'avg_temperature'                   : self._get_field_value(message_fields, 'avg_temperature'),
            'training_effect'                   : self._get_field_value(message_fields, 'total_training_effect'),
            'anaerobic_training_effect'         : self._get_field_value(message_fields, 'total_anaerobic_training_effect')
        }
        activity.update(self._plugin_dispatch('write_session_entry', self.garmin_act_db_session, fit_file, activity_id, message_fields))
        # json metadata gives better values for sport and subsport, so use existing value if set
        current = GarminDB.Activities.s_get(self.garmin_act_db_session, activity_id)
        if current:
            activity.update(self.__choose_sport(current.sport, current.sub_sport, sport, sub_sport))
            root_logger.debug("Updating with %r", activity)
            current.update_from_dict(activity, ignore_none=True, ignore_zero=True)
        else:
            activity.update({'sport': sport.name, 'sub_sport': sub_sport.name})
            root_logger.debug("Adding %r", activity)
            self.garmin_act_db_session.add(GarminDB.Activities(**activity))
        if sport is not None:
            function_name = '_write_' + sport.name + '_entry'
            try:
                function = getattr(self, function_name, None)
                if function is not None:
                    function(fit_file, activity_id, sub_sport, message_fields)
                else:
                    root_logger.warning("No sport handler for type %s from %s: %s", sport, fit_file.filename, message_fields)
            except Exception as e:
                root_logger.error("Exception in %s from %s: %s", function_name, fit_file.filename, e)
