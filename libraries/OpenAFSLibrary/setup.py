from setuptools import setup
exec(open('OpenAFSLibrary/__version__.py').read())

setup(
    name='OpenAFSLibrary',
    version=VERSION,
    description='OpenAFS Robotframework Library',
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='http://www.sinenomine.net',
    license='BSD',
    packages=[
        'OpenAFSLibrary',
        'OpenAFSLibrary.keywords',
    ],
    install_requires=[
        'robotframework',
    ],
    zip_safe=False,
)

