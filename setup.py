#!/usr/bin/env python
import os
if os.environ.get('USER','') == 'vagrant':
	del os.link

import distutils.core

distutils.core.setup(
	name = "python-asyncio-actor-system",
	version = "0.1",
	author = "Bekir Can Yalcin",
	author_email = "wtf@wtf.com",
	description = ("gevent-based actor system"),
	license = "MIT",
	url = "wtf.com",
	long_description="asyncio based actor system",
	classifiers=[
		"Development Status :: 2 - Pre-Alpha",
		"Topic :: Utilities",
		"License :: OSI Approved :: MIT License",
	],
	packages=[
        'arago.actors'
	],
	install_requires=[]
)