
#  Pynfc is a python wrapper for the libnfc library
#  Copyright (C) 2009  Mike Auty
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import os
import time
import logging
import ctypes
import string
import nfc

### NFC device setup
class NFCReader(object):
    MC_AUTH_A = 0x60
    MC_AUTH_B = 0x61
    MC_READ = 0x30
    MC_WRITE = 0xA0
    card_timeout = 10

    def __init__(self, logger):
        self.__context = None
        self.__device = None
        self.log = logger

        self._card_present = False
        self._card_last_seen = None
        self._card_uid = None
        self._card_id = None # this is the hex representation of the card id
        self._clean_card()

        mods = [(nfc.NMT_ISO14443A, nfc.NBR_106)]

        self.__modulations = (nfc.nfc_modulation * len(mods))()
        for i in range(len(mods)):
            self.__modulations[i].nmt = mods[i][0]
            self.__modulations[i].nbr = mods[i][1]

    def run(self):
        """Starts the looping thread"""
        self.__context = ctypes.pointer(nfc.nfc_context())
        nfc.nfc_init(ctypes.byref(self.__context))
        loop = True
        try:
            self._clean_card()
            conn_strings = (nfc.nfc_connstring * 10)()
            devices_found = nfc.nfc_list_devices(self.__context, conn_strings, 10)
            if devices_found >= 1: #FIXME this is just a quick hack
                self.__device = nfc.nfc_open(self.__context, conn_strings[0])
                if self.__device:
                  try:
                    _ = nfc.nfc_initiator_init(self.__device)
                    while True:
                        self._poll_loop()
                  finally:
                    nfc.nfc_close(self.__device)
            else:
                print "NFC waiting for device"
                self.log("NFC Waiting for device.")
                time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            loop = False
        except IOError, e:
            self.log("Exception: " + str(e))
            loop = True  # not str(e).startswith("NFC Error whilst polling")
        # except Exception, e:
        # loop = True
        #    print "[!]", str(e)
        finally:
            nfc.nfc_exit(self.__context)
            self.log("NFC Clean shutdown called")
        return loop

    @staticmethod
    def _sanitize(bytesin):
        """Returns guaranteed ascii text from the input bytes"""
        return "".join([x if 0x7f > ord(x) > 0x1f else '.' for x in bytesin])

    @staticmethod
    def _hashsanitize(bytesin):
        """Returns guaranteed hexadecimal digits from the input bytes"""
        return "".join([x if x.lower() in 'abcdef0123456789' else '' for x in bytesin])

    def _poll_loop(self):
        """Starts a loop that constantly polls for cards"""
        nt = nfc.nfc_target()
        res = nfc.nfc_initiator_poll_target(self.__device, self.__modulations, len(self.__modulations), 10, 2,
                                            ctypes.byref(nt))
        # print "RES", res
        if res < 0:
            raise IOError("NFC Error whilst polling")
        elif res >= 1:
            uid = None
            #if nt.nti.nai.szUidLen == 4:
            #    uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(4)])
            uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
            if uid:
                if not ((self._card_uid and self._card_present and uid == self._card_uid) and \
                                    time.mktime(time.gmtime()) <= self._card_last_seen + self.card_timeout):
                    self._setup_device()
                    self.read_card(uid)
            self._card_uid = uid
            self._card_present = True
            self._card_last_seen = time.mktime(time.gmtime())
        else:
            self._card_present = False
            self._clean_card()

    def _clean_card(self):
        self._card_uid = None

    def select_card(self):
        """Selects a card after a failed authentication attempt (aborted communications)

           Returns the UID of the card selected
        """
        nt = nfc.nfc_target()
        _ = nfc.nfc_initiator_select_passive_target(self.__device, self.__modulations[0], None, 0, ctypes.byref(nt))
        uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
        return uid

    def _setup_device(self):
        """Sets all the NFC device settings for reading from Mifare cards"""
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_ACTIVATE_CRYPTO1, True) < 0:
            raise Exception("Error setting Crypto1 enabled")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_INFINITE_SELECT, False) < 0:
            raise Exception("Error setting Single Select option")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_AUTO_ISO14443_4, False) < 0:
            raise Exception("Error setting No Auto ISO14443-A jiggery pokery")
        if nfc.nfc_device_set_property_bool(self.__device, nfc.NP_HANDLE_PARITY, True) < 0:
            raise Exception("Error setting Easy Framing property")

    def read_card(self, uid):
        """Takes a uid, reads the card and return data for use in writing the card"""
        # as of right now I don't want card data, just the UID
        key = "\xff\xff\xff\xff\xff\xff"
        card_id = uid.encode("hex")
        self.log("Read card", card_id, self._card_uid)
        self._card_id = card_id
        return
        
    def card_id(self):
      card_id = self._card_id
      self._card_id = None
      return card_id


