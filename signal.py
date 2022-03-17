#! /usr/bin/env python3

from argparse import ArgumentParser
import sys
import os

IGNORED_DIRS = {'thirdparty', 'misc', '__pycache__'}

added = set()
ADDED = 'ADD_SIGNAL(MethodInfo("'

emitted = set()
EMITTED_BARE = 'emit_signal("'
EMITTED_CORE = 'emit_signal(CoreStringNames::get_singleton()->'
EMITTED_SCENE = 'emit_signal(SceneStringNames::get_singleton()->'

connected = set()
CONNECTED = '->connect("'

compat_connected = set()
COMPAT_CONNECTED = 'connect_compat("'

def analyze_file(filename: str):
    """ Check if file contains some signals """
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip().startswith('//'):
                continue
            if ADDED in line:
                signal = line.split(ADDED)[1].split('"')[0]
                added.add(signal)
            elif EMITTED_BARE in line:
                signal = line.split(EMITTED_BARE)[1].split('"')[0]
                emitted.add(signal)
            elif EMITTED_CORE in line:
                signal = line.split(EMITTED_CORE)[1].split(')')[0].split(',')[0]
                emitted.add(signal)
            elif EMITTED_SCENE in line:
                signal = line.split(EMITTED_SCENE)[1].split(')')[0].split(',')[0]
                emitted.add(signal)
            elif CONNECTED in line:
                signal = line.split(CONNECTED)[1].split('"')[0]
                connected.add(signal)
            elif COMPAT_CONNECTED in line:
                signal = line.split(COMPAT_CONNECTED)[1].split('"')[0]
                compat_connected.add(signal)


def check_signals_in_dir(dirpath:str):
    """ Recursively check signals in files in the whole directory structure """
    content = os.listdir(dirpath)
    for file in content:
        if file.startswith('.') or file in IGNORED_DIRS:
            continue
        file = '/'.join([dirpath, file])
        if os.path.isdir(file):
            check_signals_in_dir(file)
            continue
        if not file.endswith('.cpp') and not file.endswith('.h') or file.endswith('.gen.h'):
            continue
        analyze_file(file)


if __name__ == '__main__':
    arg_parser = ArgumentParser(
        description='Find out about signal usage in Godot'
    )
    arg_parser.add_argument(
        'godot_repository',
        nargs='?',
        metavar='GDREPO',
        help='Path to an existing Godot repository'
    )
    args = arg_parser.parse_args(sys.argv[1::])
    godot_repository = args.godot_repository

    if not os.path.isdir(godot_repository):
        raise Exception(f'{godot_repository} is not a proper direcotory')

    if 'icon.svg' not in os.listdir(godot_repository):
        raise Exception(f'{godot_repository} is not a proper Godot repository')

    check_signals_in_dir(os.path.realpath(godot_repository))

    fine = added.intersection(emitted).intersection(connected)

    total = 0
    for signal in sorted(emitted.difference(added).difference(connected)):
        print(f'Signal {signal} is emitted but never added or connected')
        total += 1
    print()

    for signal in sorted(emitted.intersection(connected).difference(added)):
        print(f'Signal {signal} is emitted and connected but never added')
        total += 1
    print()

    for signal in sorted(emitted.intersection(added).difference(connected)):
        print(f'Signal {signal} is emitted and added but never connected,',
        "this is just information message which you can ignore."
        )
        total += 1
    print()

    for signal in sorted(added.difference(emitted).difference(connected)):
        print(f'Signal {signal} is added but never emitted or connected')
        total += 1
    print()

    for signal in sorted(added.intersection(connected).difference(emitted)):
        print(f'Signal {signal} is added and connected but never emitted')
        total += 1
    print()

    for signal in sorted(connected.difference(added).difference(emitted)):
        print(f'Signal {signal} is connected but never added or emitted')
        total += 1
    print()

    if total > 0:
        print('Found unused signal, exiting with code 1.')
        sys.exit(1)
