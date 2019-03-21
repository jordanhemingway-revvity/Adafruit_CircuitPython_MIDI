# The MIT License (MIT)
#
# Copyright (c) 2019 Kevin J. Walters
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import unittest
from unittest.mock import Mock, MagicMock


import os
verbose = int(os.getenv('TESTVERBOSE',2))

# adafruit_midi has an import usb_midi
import sys
sys.modules['usb_midi'] = MagicMock()

import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.system_exclusive import SystemExclusive

### To incorporate into tests
# This is using running status in a rather sporadic manner
# Acutally this now looks more like losing bytes due to being
# overwhelmed by "big" bursts of data
#
# Receiving:  ['0xe0', '0x67', '0x40']
# Receiving:  ['0xe0', '0x72', '0x40']
# Receiving:  ['0x6d', '0x40', '0xe0']
# Receiving:  ['0x5', '0x41', '0xe0']
# Receiving:  ['0x17', '0x41', '0xe0']
# Receiving:  ['0x35', '0x41', '0xe0']
# Receiving:  ['0x40', '0x41', '0xe0']

### TODO - re work these when running status is implemented

class Test_MIDIMessage_from_message_byte_tests(unittest.TestCase):
    def test_NoteOn_basic(self):
        data = bytes([0x90, 0x30, 0x7f])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 0)
        
    def test_NoteOn_awaitingthirdbyte(self):
        data = bytes([0x90, 0x30])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)
        self.assertIsNone(msg)
        self.assertEqual(msgendidxplusone, skipped,
                         "skipped must be 0 as it only indicates bytes before a status byte")
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 0,
                         "msgendidxplusone must be 0 as buffer must be lest as is for more data")
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)

    def test_NoteOn_predatajunk(self):
        data = bytes([0x20, 0x64, 0x90, 0x30, 0x32])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x32)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 5,
                         "data bytes from partial message and messages are removed" )
        self.assertEqual(skipped, 2)
        self.assertEqual(channel, 0)
        
    def test_NoteOn_prepartialsysex(self):
        data = bytes([0x01, 0x02, 0x03, 0x04, 0xf7,  0x90, 0x30, 0x32])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn,
                              "NoteOn is expected if SystemExclusive is loaded otherwise it would be MIDIUnknownEvent")
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x32)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 8,
                         "end of partial SysEx and message are removed")
        self.assertEqual(skipped, 4, "skipped only counts data bytes so will be 4 here")
        self.assertEqual(channel, 0)

    def test_NoteOn_predsysex(self):
        data = bytes([0xf0, 0x42, 0x01, 0x02, 0x03, 0x04, 0xf7,  0x90, 0x30, 0x32])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, SystemExclusive)
        self.assertEqual(msg.manufacturer_id, bytes([0x42]))   # Korg
        self.assertEqual(msg.data, bytes([0x01, 0x02, 0x03, 0x04]))
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 7)
        self.assertEqual(skipped, 4,
                         "skipped only counts data bytes so will be 4 here")
        self.assertEqual(channel, 0)        
        
        
    def test_NoteOn_postNoteOn(self):
        data = bytes([0x90 | 0x08, 0x30, 0x7f,  0x90 | 0x08, 0x37, 0x64])
        ichannel = 8

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3)
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 8)

    def test_NoteOn_postpartialNoteOn(self):
        data = bytes([0x90, 0x30, 0x7f,  0x90, 0x37])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x30)
        self.assertEqual(msg.velocity, 0x7f)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3, 
                         "Only first message is removed")
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 0)

    def test_NoteOn_preotherchannel(self):
        data = bytes([0x90 | 0x05, 0x30, 0x7f,  0x90 | 0x03, 0x37, 0x64])
        ichannel = 3

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, NoteOn)
        self.assertEqual(msg.note, 0x37)
        self.assertEqual(msg.velocity, 0x64)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 6,
                         "Both messages are removed from buffer")
        self.assertEqual(skipped, 0)
        self.assertEqual(channel, 3)

    def test_NoteOn_partialandpreotherchannel(self):
        data = bytes([0x95, 0x30, 0x7f,  0x93, 0x37])
        ichannel = 3

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsNone(msg)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 3,
                         "first message removed, second partial left")
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)

    def test_Unknown_SinglebyteStatus(self):
        data = bytes([0xfd])
        ichannel = 0

        (msg, startidx, msgendidxplusone, skipped, channel) =  adafruit_midi.MIDIMessage.from_message_bytes(data, ichannel)

        self.assertIsInstance(msg, adafruit_midi.midi_message.MIDIUnknownEvent)
        self.assertEqual(startidx, 0)
        self.assertEqual(msgendidxplusone, 1)
        self.assertEqual(skipped, 0)
        self.assertIsNone(channel)


if __name__ == '__main__':
    unittest.main(verbosity=verbose)
