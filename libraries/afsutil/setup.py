from setuptools import setup

setup(name='afsutil',
      version='0.4',
      description='Utilities to setup OpenAFS clients and servers',
      author='Michael Meffie',
      author_email='mmeffie@sinenomine.net',
      license='BSD',
      packages=['afsutil'],
      scripts=['scripts/afsutil'],
      zip_safe=False)

