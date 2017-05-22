from setuptools import setup
from afsutil import __version__

setup(
    name='afsutil',
    version=__version__,
    description='Utilities to setup OpenAFS clients and servers',
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='http://www.sinenomine.net',
    license='BSD',
    packages=['afsutil'],
    scripts=['scripts/afsutil'],
    package_data={'afsutil':['data/*.init']},
    include_package_data=True,
    test_suite='test',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
)

