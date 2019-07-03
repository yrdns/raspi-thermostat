from RPi_I2C_driver.RPi_I2C_driver import lcd

import logging
import threading
import time

class displayControl():
    def __init__(self, counter_flash=False):
        self.lock = threading.Condition()
        self.counter_thread = None

        self.display = lcd()
        self.display.lcd_load_custom_chars(
            [ # Degree symbol
             [0x02, 0x05, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00],
              # Alternate colon
             [0x00, 0x00, 0x04, 0x00, 0x00, 0x04, 0x00, 0x00],
            ])

        self.counter_flash = counter_flash
        self.counter_offsettime = None
        self.counter_starttime = None

        self.to_delete = False
        self.counter_thread = threading.Thread(target=self.counterThread)
        self.counter_thread.daemon = True
        self.counter_thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        self.display.lcd_clear()

        while (self.counter_thread and not self.counter_thread.join(0) and
               self.counter_thread.is_alive()):
            self.lock.notify()
            self.lock.wait()
        self.lock.release()

    def clear(self):
        self.display.lcd_clear()

    def startCounter(self, runtime, starttime):
        self.lock.acquire()
        self.counter_offsettime = runtime
        self.counter_starttime = starttime

        self.lock.notify()
        self.lock.release()

    def stopCounter(self, new_runtime):
        self.lock.acquire()
        self.counter_offsettime = new_runtime
        self.counter_starttime = None

        self.updateDisplay(runtime=new_runtime)

        self.lock.release()

    def counterThread(self):
        self.lock.acquire()
        while not self.to_delete:
            if self.counter_starttime == None:
                self.lock.wait()
            else:
                cur_time = time.time()
                display_time = (self.counter_offsettime +
                                (cur_time - self.counter_starttime))
                self.updateDisplay(runtime = display_time,
                                   tick = not self.counter_flash or
                                          display_time%1.0 >= .5)

                cur_time = time.time()
                display_time = (self.counter_offsettime +
                                (cur_time - self.counter_starttime))
                if self.counter_flash:
                    self.lock.wait(.5 - display_time%.5)
                else:
                    self.lock.wait(1.0 - display_time%1.0)

        self.lock.release()

    def updateDisplay(self, temp=None, target=None,
                      status=None, runtime=None, tick=True):
        self.lock.acquire()
        # First Line
        if temp != None:
            l1 = "     Temp:%7.2f"   % temp

            self.display.lcd_display_string(l1, 1)
            self.display.lcd_write_char(0) # Degree sign
            self.display.lcd_write_char(ord("F"))
            for i in range(20 - 2 - len(l1)):
                self.display.lcd_write_char(ord(" "))

        # Second Line
        if target != None:
            l2 = "   Target:%7.2f"   % target
            self.display.lcd_display_string(l2, 2)
            self.display.lcd_write_char(0) # Degree sign
            self.display.lcd_write_char(ord("F"))
            for i in range(20 - 2 - len(l2)):
                self.display.lcd_write_char(ord(" "))

        # Third Line
        if status != None:
            status *= 100
            l3 = " On Value:%7.2f%%" % status
            self.display.lcd_display_string(l3, 3)
            for i in range(20 - len(l3)):
                self.display.lcd_write_char(ord(" "))

        # Fourth Line
        if runtime != None:
            runtime = int(runtime + .5)
            l4 = "  Runtime:%3d-%02d-%02d" % (runtime // 3600,
                                              (runtime % 3600) // 60,
                                              runtime % 60)
            l4_split = l4.split("-")
            self.display.lcd_display_string(l4_split[0], 4)
            for s in l4_split[1:]:
                if tick:
                    self.display.lcd_write_char(1) # Colon (alternate)
                else:
                    self.display.lcd_write_char(ord(" "))
                self.display.lcd_display_string(s, 0)
            for i in range(20 - len(l4)):
                self.display.lcd_write_char(ord(" "))

        self.lock.release()

