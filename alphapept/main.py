version = "0.0.1"

def alphapept_screen(version):
    """
    Prints an Ascii-Art logo and version number
    """
    project_name = "AlphaPept" + " " + version

    print("\n")
    print(r"     ___    __      __          ____             __ ")
    print(r"    /   |  / /___  / /_  ____ _/ __ \___  ____  / /_")
    print(r"   / /| | / / __ \/ __ \/ __ \/ /_/ / _ \/ __ \/ __/")
    print(r"  / ___ |/ / /_/ / / / / /_/ / ____/  __/ /_/ / /_  ")
    print(r" /_/  |_/_/ .___/_/ /_/\__,_/_/    \___/ .___/\__/  ")
    print(r"         /_/                          /_/           ")
    print("\n")
    print(project_name)
    print('Mann Labs')
    print("\n")



def main():

    import argparse

    # Main parser
    parser = argparse.ArgumentParser("alphapept")
    subparsers = parser.add_subparsers(dest="command")

    gui_parser = subparsers.add_parser("gui", help="Open the AlphaPept GUI")

    # link parser
    sampledb_parser = subparsers.add_parser(
        "sampledb", help="Create a sample-specific database"
    )
    sampledb_parser.add_argument("rawfile", help=("Path to rawfile"))
    sampledb_parser.add_argument("fasta", help=("Path to fastafile"))
    sampledb_parser.add_argument(
        "-s",
        "--score",
        type=int,
        default=10,
        help=(
            "Minimum score to keep entry in fasta file. The Score is sum of the number of peptide hits (Default = 10) "
        ),
    )

    alphapept_screen(version)


    args = parser.parse_args()
    if args.command:
        if args.command == "gui":
            print("gui")
            from alphapept.gui import search

            search.main()

        if args.command == "sampledb":
            print(sampledb)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
