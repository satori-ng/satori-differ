from setuptools import setup

import satoridiffer

setup(
    name=satoridiffer.__name__,
    description=satoridiffer.__desc__,
    version=satoridiffer.__version__,

    author="Satori-NG org",
    author_email=satoridiffer.__email__,

    packages=["satoridiffer"],

    # entry_points={
    #     "console_scripts": [
    #         "hexwordify=hexwordify.__main__:main",
    #     ],
    # },
)
