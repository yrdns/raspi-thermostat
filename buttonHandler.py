from buttonGPIO import buttonGPIO
from buttonKeyboard import buttonKeyboard

import logging

def buttonHandler(button, callback):
    try:
        if isinstance(button, str):
            return buttonKeyboard(button, callback)
        else:
            return buttonGPIO(button, callback)
    except Exception as err:
        logging.error("Failed to initialize button of type %s: %s"
                       % (button, err))
    return None
