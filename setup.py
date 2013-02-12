from setuptools import setup

setup(
    name='bookingcom',
    packages=['bookingcom'],
    version='0.0.1',
    description='booking.com api client',
    author='Metglobal',
    author_email='kadir.pekel@metglobal.com',
    url='https://github.com/metglobal/bookingcom',
    install_requires=[
        'requests',
        'xmltodict'
    ],
    tests_require=[
        'httpretty',
        'mock'
    ],
)
