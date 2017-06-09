from setuptools import setup
from afsrobot import __version__

setup(name='afsrobot',
      version=__version__,
      description='OpenAFS Robotest Runner',
      author='Michael Meffie',
      author_email='mmeffie@sinenomine.net',
      url='http://www.sinenomine.net',
      license='BSD',
      packages=['afsrobot'],
      install_requires=[
          'afsutil>=0.6.6',
          'robotframework'
      ],
      scripts=['scripts/afsrobot', 'scripts/afs-robotest'],
      test_suite='test',
      zip_safe=False)

