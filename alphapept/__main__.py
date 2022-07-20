#!/usr/bin/env python


from .__version__ import VERSION_NO
from .__version__ import COPYRIGHT
from .__version__ import URL
import logging

def main():
    try:
        import alphapept.interface
        alphapept.interface.run_cli()
    except Exception as e:
        print(f'\nAn exception occured running AlphaPept version {VERSION_NO}:\n')
        print('.'*52)
        print(f"\n{e}\n")
        logging.exception('Traceback')

        if 'No module named' in str(e):
            print('\nPlease make sure to run AlphaPept in the right environment and have all required python packages installed (pip install -r requirements.txt).')
        else:
            print('\nPlease visit https://github.com/MannLabs/alphapept and report this issue or search for potential solutions. Thanks.\n')

        print('.'*52)

        if not alphapept.interface.HEADLESS:
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
