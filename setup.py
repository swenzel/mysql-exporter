from setuptools import setup

setup(
    name='mysql_exporter',
    version='0.0.1',
    install_requires=[ "pymysql~=0.9", "click~=7.0", "pyyaml~=5.1" ],
    python_requires='>=3.6.*, <4',
    entrypoint={
        "console_scripts":["mysqlexport:mysqlexport.main"]
    },
    classifiers=[
        # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Database Administrators',
        'Topic :: Database Administration :: Extraction Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)