#!/usr/bin/env python
import os
if os.environ.get('USER','') == 'vagrant':
	del os.link

import distutils.core

distutils.core.setup(
	name = "python-asyncio-actor-model",
	version = "0.1",
	author = "Bekir Can Yalcin",
	author_email = "wtf@wtf.com",
	description = ("asyncio based actor model"),
	license = "WTFPL",
	url = "wtf.com",
	long_description="asyncio based actor model",
	classifiers=[
		"Development Status :: 2 - Pre-Alpha",
		"Topic :: Utilities",
		"License :: OSI Approved :: WTFPL License",
	],
	packages=[
        'minions.actors',
        'minions.actors.custom.routers',
	],
	install_requires=[]
)