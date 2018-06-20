from setuptools import setup

import satoridiffer

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name=satoridiffer.__name__,
    description=satoridiffer.__desc__,
    version=satoridiffer.__version__,

    author="Satori-NG org",
    author_email=satoridiffer.__email__,

    packages=['satoridiffer'],

    entry_points={
        "console_scripts": [
            "satori-differ=satoridiffer.__main__:main",
        ],
    },
    install_requires=requirements,

)


