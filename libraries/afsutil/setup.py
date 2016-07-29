from setuptools import setup

execfile("./afsutil/__init__.py") # sets __version__
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
      zip_safe=False)

