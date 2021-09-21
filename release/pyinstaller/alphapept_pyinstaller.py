if __name__ == "__main__":
    try:
        import alphapept.gui
        import multiprocessing
        multiprocessing.freeze_support()
        alphapept.gui.run()
    except e:
        import traceback
        import sys
        exc_info = sys.exc_info()
        # Display the *original* exception
        traceback.print_exception(*exc_info)
        input("Something went wrong, press any key to continue...")
