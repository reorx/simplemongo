try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


version = '0.1.dev1'


setup(
    name='simplemongo',
    version=version,
    packages=['simplemongo', 'simplemongo.test'],
    author='reorx',
    author_email='novoreorx@gmail.com',
    url='https://github.com/reorx/simplemongo',
    license='http://opensource.org/licenses/MIT',
    description='Simplemongo is a MongoDB ORM designed for simplicity and scalability.',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 2 - Pre-Alpha'
    ],
    install_requires=['pymongo']
)
