#!/usr/bin/python3
import logging
import os
import threading

from kaffeekasse.controller import CoffeeFundController
from kaffeekasse.database import create_debug_database
from kaffeekasse.nfcmonitor import NfcMonitor
from kaffeekasse.qtguicontroller import QtGuiController


def main():
    logger = logging.getLogger(__name__)

    logger.info("starting")

    # switch working directory to this file's directory to keep loading styles for GUI working
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    controller = CoffeeFundController()

    nfc_monitor = NfcMonitor()
    nfc_monitor.register(controller.enqueue_event)
    nfc_thread = threading.Thread(target=nfc_monitor.run_event_loop, daemon=True)
    nfc_thread.start()

    controller_thread = threading.Thread(target=controller.run_event_loop, daemon=True)
    controller_thread.start()

    gui_controller = QtGuiController(controller)
    controller.register(gui_controller.apply_state_change)
    gui_controller.run()

    nfc_thread.join()
    logger.error("worker threads exited, shutting down")

if __name__ == "__main__":
    if not os.getenv("KAFFEEKASSE_DEBUG") is None:
        logging.basicConfig(level=logging.DEBUG)
        create_debug_database()
    else:
        logging.basicConfig(level=logging.WARN)
    main()
    logging.shutdown()