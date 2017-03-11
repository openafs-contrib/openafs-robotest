from setuptools import setup
from OpenAFSLibrary.version import VERSION

setup(name='OpenAFSLibrary',
      version=VERSION,
      description='OpenAFS Robotframework Library',
      author='Michael Meffie',
      author_email='mmeffie@sinenomine.net',
      url='http://www.sinenomine.net',
      license='BSD',
      packages=['OpenAFSLibrary', 'OpenAFSLibrary.keywords'],
      zip_safe=False)

