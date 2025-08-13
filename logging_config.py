# logging_config.py

import os
import logging
import sys

os.makedirs('database', exist_ok=True)

# Create a custom StreamHandler that handles Unicode properly on Windows
class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Use UTF-8 encoding for Windows console
            if sys.platform == 'win32':
                stream.buffer.write(msg.encode('utf-8'))
                stream.buffer.write(b'\n')
                stream.buffer.flush()
            else:
                stream.write(msg + self.terminator)
                self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s|%(levelname)s|%(module)s|%(message)s',
    handlers=[
        logging.FileHandler('database/cms_wizard.log', encoding='utf-8'),
        UnicodeStreamHandler()
    ]
)
logger = logging.getLogger(__name__)
