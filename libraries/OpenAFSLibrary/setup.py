from setuptools import setup

execfile("./OpenAFSLibrary/version.py") # sets VERSION

setup(name='OpenAFSLibrary',
      version=VERSION,
      description='OpenAFS Robotframework Library',
      author='Michael Meffie',
      author_email='mmeffie@sinenomine.net',
      license='BSD',
      packages=['OpenAFSLibrary', 'OpenAFSLibrary.keywords'],
      zip_safe=False)

