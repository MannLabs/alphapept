#!/usr/bin/env python


from .__version__ import VERSION_NO
from .__version__ import COPYRIGHT
from .__version__ import URL


def main():
    try:
        import alphapept.interface
        alphapept.interface.run_cli()
    except Exception as e:
        print(f'\nAn exception occured running AlphaPept version {VERSION_NO}:\n')
        print('.'*52)
        print(f"\n{e}\n")
        print('.'*52)
        print('Please visit https://github.com/MannLabs/alphapept and report this issue. Thanks.\n')

        input("Press Enter to continue...")

if __name__ == "__main__":
    main()
