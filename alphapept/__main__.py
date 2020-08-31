#!/usr/bin/env python
"""
    alphapept.__main__.py
    ~~~~~~~~~~~~~~~~
    AlphaPept command line interface
    :authors: Maximilian Thomas Strauss
    :copyright: Copyright (c) 2020 Mann Labs
"""

import os


from alphapept.__version__ import VERSION_NO
from alphapept.__version__ import COPYRIGHT
from alphapept.__version__ import URL


def _run_alphapept(args):
    import alphapept.runner
    import alphapept.settings

    if os.path.isfile(args.settings_path):
        _settings = alphapept.settings.load_settings(args.settings_path)
        alphapept.runner.run_alphapept(_settings)


def _convert(args):
    import alphapept.io
    if os.path.isfile(args.rawfile):
        abundant = args.abundant
        settings = {}
        settings['raw'] = {}
        settings['raw']['most_abundant'] = abundant
        to_process = (args.rawfile, settings)
        alphapept.io.raw_to_npz(to_process)


def _database(args):
    raise NotImplementedError


def _features(args):
    raise NotImplementedError


def _search(args):
    raise NotImplementedError


def main():
    import argparse
    # Main parser
    parser = argparse.ArgumentParser("alphapept")

    subparsers = parser.add_subparsers(dest="command")

    workflow_parser = subparsers.add_parser(
        "workflow", help="Process files with alphapept using a settings file."
    )
    workflow_parser.add_argument(
        "settings_path", help=("Path to settings file")
    )

    gui_parser = subparsers.add_parser("gui", help="Open the AlphaPept GUI.")
    gui_parser.add_argument(
        "--test",
        required=False,
        help=("Flag to open and close gui for testing purposes.")
    )

    convert_parser = subparsers.add_parser(
        'convert',
        help='Perform file conversion on a raw file for AlphaPept.'
    )
    convert_parser.add_argument("rawfile", help=("Path to rawfile"))
    convert_parser.add_argument(
        "-a",
        "--abundant",
        type=int,
        default=400,
        help=(
            "Number of most abundant peaks to keep. (Default = 400) "
        ),
    )

    database_parser = subparsers.add_parser(
        'database',
        help='Create a AlphaPept compatible database from a FASTA file.'
    )

    database_parser.add_argument("fastafile", help=("Path to FASTA file."))
    database_parser.add_argument(
        "-a",
        "--abundant",
        type=int,
        default=400,
        help=(
            "Number of most abundant peaks to keep. (Default = 400) "
        ),
    )

    # feature_finder_parser = subparsers.add_parser(
    #     'features',
    #     help='Find features on a specific file.'
    # )
    # search_parser = subparsers.add_parser(
    #     'search',
    #     help=   'Search a converted raw file against a AlphaPept compatible '
    #             'database.'
    # )
    # watcher_parser = subparsers.add_parser(
    #     'watcher',
    #     help=   'Continuously monitor a folder and perform file conversion '
    #             'and feature finding.'
    # )
    # link parser

    print("\n")
    print(r"     ___    __      __          ____             __ ")
    print(r"    /   |  / /___  / /_  ____  / __ \___  ____  / /_")
    print(r"   / /| | / / __ \/ __ \/ __ \/ /_/ / _ \/ __ \/ __/")
    print(r"  / ___ |/ / /_/ / / / / /_/ / ____/ ___/ /_/ / /_  ")
    print(r" /_/  |_/_/ .___/_/ /_/\__,_/_/    \___/ .___/\__/  ")
    print(r"         /_/                          /_/           ")
    print('.'*52)
    print('.{}.'.format(URL.center(50)))
    print('.{}.'.format(COPYRIGHT.center(50)))
    print('.{}.'.format(VERSION_NO.center(50)))
    print('.'*52)

    args = parser.parse_args()
    if args.command:

        if args.command == "workflow":
            if args.settings_path:
                _run_alphapept(args)

        if args.command == "gui":
            print('Launching GUI')
            from . import ui as _ui
            if args.test:
                _ui.main(close=True)
            else:
                _ui.main()

        if args.command == "convert":
            print('Convert')
            _convert(args)

        if args.command == "database":
            _database(args)

        if args.command == "features":
            _features(args)

        if args.command == "search":
            _search(args)

        if args.command == "watcher":
            print('Launching Watcher')
            from . import watcher as _watcher
            _watcher.main()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
