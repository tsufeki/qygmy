#!/usr/bin/env python3

import logging
logger = logging.getLogger('qygmy')
logger.setLevel(logging.DEBUG)
c = logging.StreamHandler()
c.setLevel(logging.DEBUG)
logger.addHandler(c)

import qygmy.qygmy
qygmy.qygmy.main()
