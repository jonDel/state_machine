from setuptools import setup, find_packages

setup(
    name='state_machine_db',
    version='0.1',
    author='Jonatan Dellagostin',
    author_email='jdellagostin@gmail.com',
    url='https://github.com/jonDel/state_machine_db',
    packages=find_packages(),
    license='GPLv3',
    description='Provides the implementation of a configurable state machine',
    long_description=open('README.rst').read(),
    classifiers=[
     'Development Status :: 3 - Alpha',
     'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
     'Programming Language :: Python :: 2.6',
     'Programming Language :: Python :: 2.7',
     'Topic :: System :: Shells',
    ],
    keywords='state machine finite',
    install_requires=[
    ],
)
