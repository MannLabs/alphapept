#!/usr/bin/env python


from .__version__ import VERSION_NO
from .__version__ import COPYRIGHT
from .__version__ import URL


def main():
    import alphapept.interface
    alphapept.interface.run_cli()


if __name__ == "__main__":
    main()
