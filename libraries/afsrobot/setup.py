from setuptools import setup

execfile("./afsrobot/__init__.py") # sets __version__
setup(name='afsrobot',
      version=__version__,
      description='OpenAFS Robotest Runner',
      author='Michael Meffie',
      author_email='mmeffie@sinenomine.net',
      url='http://www.sinenomine.net',
      license='BSD',
      packages=['afsrobot'],
      scripts=['scripts/afs-robotest'],
      zip_safe=False)

