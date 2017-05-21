from setuptools import setup
from afsutil import __version__

setup(name='afsutil',
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
      zip_safe=False)

