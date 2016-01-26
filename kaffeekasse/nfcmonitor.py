import logging
import random
from time import sleep

from kaffeekasse.pn532 import PN532
from kaffeekasse.utils.observer import Event, Observable

logger = logging.getLogger(__name__)


# PIN setup - adjust this to match your connections
CS = 8
MOSI = 10
MISO = 9
SCLK = 11

Poll_Wait_Time_Seconds = 0.2


class NfcEvent(Event):
    def __init__(self, uid):
        self.uid = uid
        self.invalid = False


class NfcEventFactory:
    none_event = None

    @classmethod
    def create_nfc_event(cls, uid) -> NfcEvent:
        return NfcEvent(uid)

    @classmethod
    def create_none_nfc_event(cls) -> NfcEvent:
        if cls.none_event is None:
            cls.none_event = NfcEvent(-1)
            cls.none_event.invalid = True
        return cls.none_event


class NfcMonitor(Observable):
    def __init__(self):
        super(NfcMonitor, self).__init__()
        self._pn532 = None
        self.setup_pn532()

    def setup_pn532(self):
        logger.debug("setting up PN532 NFC reader")
        self._pn532 = PN532.PN532(CS, SCLK, MOSI, MISO)
        self._pn532.begin()
        ic, ver, rev, support = self._pn532.get_firmware_version()
        logger.info("Found PN532 reader with firmware version: {0}.{1}, ic: {2}".format(ver, rev, ic))
        self._pn532.SAM_configuration()
        logger.debug("successfully set up PN532 NFC reader")
        pass

    def run_event_loop(self):
        while True:
            logger.debug("attempting to read NFC UID")
            try:
                uid = self._pn532.read_passive_target()
                if uid is None:
                    event = NfcEventFactory.create_none_nfc_event()
                else:
                    # it seems UIDs are little endian, but it does not really matter
                    uid_as_int = int.from_bytes(uid, byteorder='little', signed=False)
                    event = NfcEventFactory.create_nfc_event(uid_as_int)
                self.notify_all(event)
            except RuntimeError as e:
                logger.error("Error while polling NFC (maybe result of unstable connection)")
                logger.error(e)

            sleep(Poll_Wait_Time_Seconds)


class NfcMonitorStub(Observable):
    def __init__(self):
        super(NfcMonitorStub, self).__init__()

    def run_event_loop(self):
        while True:
            rand = random.random()
            if rand < 0.1:
                event = NfcEvent(0xdeadbeef)
                self.notify_all(event)
            sleep(Poll_Wait_Time_Seconds)
