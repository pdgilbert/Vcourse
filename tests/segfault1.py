#!/usr/bin/python3

# This test needs Raspberry Pi hardware

# need  export PYTHONPATH=/path/to/Vcourse/lib

import LED_piZeroW   as LEDs

LEDs.off()
LEDs.warn()
LEDs.bound()
LEDs.warn()
LEDs.off()

# above maybe twice, then
#>>> Segmentation fault

#also

LEDs.bound()
LEDs.warn()
LEDs.off()

#after a few seconds
#>>> Segmentation fault
