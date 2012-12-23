''' Unified logging setup for all macro libraries and scripts.
Lets me control logging easily and in one place. '''

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='[%(module)s] %(levelname)s %(funcName)s(): %(message)s')

logger = logging.getLogger('macro')




