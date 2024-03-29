import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.version_info < (3, 10, 0):
    raise RuntimeError("Gru says, that minions require Python 3.10.0+")


setup(
    name="python-asyncio-actor-system",
    version="0.1",
    author="Bekir Can Yalcin",
    author_email="wtf@wtf.com",
    description=("asyncio based actor system"),
    license="WTFPL",
    url="wtf.com",
    long_description="asyncio based actor system",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: WTFPL License",
    ],
    packages=[
        "minions.actors",
        "minions.actors.custom.routers",
        "minions.actors.custom.sources",
    ],
    install_requires=["falcon", "uvicorn"],
)
