#!/usr/bin/env python3

"""Script for importing into a DB and summarizing CSV formatted Microsoft Health export data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import argparse
import logging

import MSHealthDB
from import_mshealth_csv import MSHealthData, MSVaultData
from analyze_mshealth import Analyze
from garmin_db_config_manager import GarminDBConfigManager
from version import format_version


logging.basicConfig(filename='mshealth.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def __usage(program):
    print('%s -i <inputfile>' % program)
    sys.exit()


def main(argv):
    """Import and analyze Microsoft Health data."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    modes_group = parser.add_argument_group('Modes')
    modes_group.add_argument("-i", "--input_file", help="Specifiy the CSV file to import into the database")
    modes_group.add_argument("--delete_db", help="Delete MSHealth db file.", action="store_true", default=False)
    args = parser.parse_args()

    root_logger = logging.getLogger()
    if args.trace:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params = GarminDBConfigManager.get_db_params()

    if args.delete_db:
        MSHealthDB.MSHealthDB.delete_db(db_params)
        sys.exit()

    mshealth_dir = GarminDBConfigManager.get_or_create_mshealth_dir()
    metric = GarminDBConfigManager.get_metric()

    msd = MSHealthData(args.input_file, mshealth_dir, db_params, metric, args.trace)
    if msd.file_count() > 0:
        msd.process_files()

    mshv = MSVaultData(args.input_file, mshealth_dir, db_params, metric, args.trace)
    if mshv.file_count() > 0:
        mshv.process_files()

    analyze = Analyze(db_params)
    analyze.get_years()
    analyze.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
