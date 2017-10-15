import os
from codecs import open
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file; convert to .rst is possible
try:
    import pypandoc
    long_description = pypandoc.convert_file(os.path.join(here, 'README.md'), 'rst')
except (IOError, ImportError):
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='wildpath',
    version='0.2.2',
    description='easy data structure access utility',
    long_description=long_description,
    author='Lars van Gemerden',
    author_email='gemerden@gmail.com',
    license='MIT License',
    packages=['wildpath'],
    install_requires=['boolean.py'],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    # python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4',
    keywords='access data structure getter setter deleter iterator utility tool',
)
