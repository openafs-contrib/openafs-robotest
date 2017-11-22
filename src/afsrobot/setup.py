from setuptools import setup
exec(open('afsrobot/__version__.py').read())

setup(name='afsrobot',
    version=VERSION,
    description='OpenAFS Robotest Runner',
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='http://www.sinenomine.net',
    license='BSD',
    packages=['afsrobot'],
    install_requires=[
        # 'afsutil', do not install this one from the index yet
        'robotframework',
    ],
    scripts=['scripts/afsrobot'],
    test_suite='test',
    zip_safe=False,
)
