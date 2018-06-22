try:
    from setuptools import setup
except ImportError:
    # Fallback to the standard library distutils.
    from distutils.core import setup

exec(open('afsrobot/__version__.py').read())

setup(name='afsrobot',
    version=VERSION,
    description='OpenAFS Robotest Runner',
    long_description=open('README.rst').read(),
    author='Michael Meffie',
    author_email='mmeffie@sinenomine.net',
    url='http://www.sinenomine.net',
    license='BSD',
    packages=['afsrobot'],
    install_requires=[
        # 'afsutil', do not install this one from the index yet
        # 'robotframework-openafs',
        'robotframework',
    ],
    scripts=['scripts/afsrobot'],
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
