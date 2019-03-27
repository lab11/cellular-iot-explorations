#! /usr/bin/env python3

# Mostly lifted from:
#   https://github.com/pyserial/pyserial/blob/master/examples/at_protocol.py
#   https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.threaded.ReaderThread

import arrow
import random
import serial
import serial.threaded
import statistics
import sys
import threading
import time
import traceback
import queue


class ATException(Exception):
    pass

class ATProtocol(serial.threaded.LineReader):

    TERMINATOR = b'\r\n'

    def __init__(self):
        super(ATProtocol, self).__init__()
        self.alive = True
        self.responses = queue.Queue()
        self.events = queue.Queue()
        self._event_thread = threading.Thread(target=self._run_event)
        self._event_thread.daemon = True
        self._event_thread.name = 'at-event'
        self._event_thread.start()
        self.lock = threading.Lock()

        self.start_timestamp = None
        self.end_timestamp = None
        self.successful = False

    def stop(self):
        """
        Stop the event processing thread, abort pending commands, if any.
        """
        self.alive = False
        self.events.put(None)
        self.responses.put('<exit>')

    def _run_event(self):
        """
        Process events in a separate thread so that input thread is not
        blocked.
        """
        while self.alive:
            try:
                self.handle_event(self.events.get())
            except:
                print("Error in _run_event")

    def handle_line(self, line):
        """
        Handle input from serial port, check for events.
        """
        if line.startswith('+'):
            self.events.put(line)
        else:
            self.responses.put(line)

    def handle_event(self, event):
        """
        Spontaneous message received.
        """
        if self.start_timestamp:
            if event.startswith("+UUHTTPCR:"):
                self.end_timestamp = arrow.utcnow()
                result = event.split(',')[-1]
                if result == '1':
                    self.successful = True
                else:
                    self.successful = False


        print(' * {}'.format(event))

    def command(self, command, response='OK', timeout=1, error=True):
        """
        Set an AT command and wait for the response.
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(command)
            lines = []
            while True:
                try:
                    line = self.responses.get(timeout=timeout)
                    if line == response:
                        print(" * {} -> {}".format(command, line))
                        return lines
                    else:
                        lines.append(line)
                except queue.Empty:
                    if error:
                        raise ATException('AT command timeout ({!r})'.format(command))
                    else:
                        print(' * {} -> ""'.format(command))
                        return ""

    def timed_command(self, command, response='OK', timeout=1, error=True):
        self.successful = False
        self.end_timestamp = None
        self.start_timestamp = arrow.utcnow()
        res = self.command(command, response, timeout, error)

        # wait for event
        while self.end_timestamp == None:
            time.sleep(0.1)

        timediff = (self.end_timestamp - self.start_timestamp).total_seconds()
        return (res, timediff, self.successful)



class SARA_R4_N4(ATProtocol):

    def __init__(self):
        super(SARA_R4_N4, self).__init__()
        self.event_responses = queue.Queue()
        self._awaiting_response_for = None

    def connection_made(self, transport):
        super(SARA_R4_N4, self).connection_made(transport)
        print("~~Connection Opened~~")

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        print("~~Connection Closed~~")



if __name__ == '__main__':
    # configurations
    # LTE-M
    MODEM_PATH = '/dev/ttyUSB0'
    PAYLOAD_SIZES = [10, 100, 1000, 10000]

    # NB-IoT
    #MODEM_PATH = '/dev/ttyACM0'
    #PAYLOAD_SIZES = [10, 100, 1000]

    SERVER_IP = '192.154.4.152'
    SERVER_PORT= 5000
    REPEATS = 10

    port = serial.Serial(MODEM_PATH, 115200)
    with serial.threaded.ReaderThread(port, SARA_R4_N4) as modem:
        modem.command('AT')
        print("")

        print("Checking status")
        modem.command('AT+CFUN?')
        modem.command('AT+CGDCONT?')
        modem.command('AT+CEREG?')
        print("")

        print("Setting up files")
        modem.command('AT+ULSTFILE')
        modem.command('AT+ULSTFILE=1')
        for size in sorted(PAYLOAD_SIZES):
            # delete files if already existing
            modem.command('AT+UDELFILE="post{}"'.format(size), timeout=0.1, error=False)
            # create files
            modem.command('AT+UDWNFILE="post{}",{}'.format(size, size), timeout=0.1, error=False)
            # write data to the file
            # sometimes bytes are lost here, so we keep repeatedly writing until we get the OK
            res = ''
            while res == '':
                res = modem.command('a'*int(size/2), timeout=0.5, error=False)
                print(res)
            modem.command('AT')
        modem.command('AT+ULSTFILE')
        time.sleep(0.1)
        print("")

        print("Setting up http")
        modem.command('AT+UHTTP=0,0,"{}"'.format(SERVER_IP))
        modem.command('AT+UHTTP=0,4,0')
        modem.command('AT+UHTTP=0,5,{}'.format(SERVER_PORT))
        print("")

        print("Setup complete!")

        # functions to post or get data
        def post(count):
            res = modem.timed_command('AT+UHTTPC=0,4,"/{}","","post{}",1'.format(count, count))
            return res

        def get(count):
            res = modem.timed_command('AT+UHTTPC=0,1,"/{}",""'.format(count))
            return res

        print("Beginning test")
        for name,func in [("POST", post), ("GET", get)]:
            results = {}
            for size in PAYLOAD_SIZES:
                results[size] = []

            while not all([len(results[key]) == REPEATS for key in PAYLOAD_SIZES]):
                size = random.choice([key for key in PAYLOAD_SIZES if len(results[key]) < REPEATS])
                print("{}ing {} bytes".format(name, size))
                res = func(size)
                if res[2]:
                    results[size].append(res[1])
                else:
                    print("Attempt Failed")
                time.sleep(10)

            print("{} results:".format(name))
            print(results)
            for size in sorted(PAYLOAD_SIZES):
                print(size)
                print('\tAverage {}'.format(statistics.mean(results[size])))

    print("Complete!")

