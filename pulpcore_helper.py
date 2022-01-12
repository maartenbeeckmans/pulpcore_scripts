#!/usr/bin/env python3

"""
Wrapper script for managing pulpcore
"""

import argparse
import configparser
import sys

from rpm.cherry_pick.main import RpmCherryPick

def main(input_args):
    parser = argparse.ArgumentParser(description="Pulpcore helper script for managing pulpcore")

    parser.add_argument('plugin', help='Pulpcore plugin to use for the action')
    parser.add_argument('action', help='Action to use. Like cherry_pick')

    parser.add_argument('-c', "--config", dest='configfile', default="config.ini", help="Path to pulpcore_helper.py configuration file")
    parser.add_argument('-d', "--data-file", dest='datafile', default='cherrypick.yaml', help="Path to cherry_pick data file")

    args = parser.parse_args(input_args)

    config = configparser.ConfigParser()
    with open(args.configfile) as fp:
      config.read_file(fp)

    pulpcore_config = config['pulpcore']
    if args.plugin == 'rpm':
        if args.action == 'cherry_pick':
            print('cherry picking rpm')
            cherry_pick_rpm = RpmCherryPick(
              args.datafile,
              pulpcore_config['host'],
              pulpcore_config['username'],
              pulpcore_config['password']
            )
            cherry_pick_rpm.cherry_pick()
        else:
            print('only cherry_pick is supported for rpm plugin')
            sys.exit(1)
    else:
        print('only rpm plugin is supported')
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
