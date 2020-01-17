from setuptools import setup


setup(
    name='wildpath3',
    version='0.3.0',
    description='easy data structure access utility',
    long_description='see <https://github.com/gemerden/wildpath>',
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
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.3',
    keywords='access data structure getter setter deleter iterator utility tool path wildcard slice',
)
