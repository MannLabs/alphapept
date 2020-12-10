from multiprocessing import freeze_support

if __name__ == "__main__":
    # This line is needed so that pyinstaller can handle multiprocessing
    freeze_support()
    from alphapept.__main__ import main

    main()