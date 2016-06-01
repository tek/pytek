from setuptools import setup, find_packages

version_parts = (3, 3, 0)
version = '.'.join(map(str, version_parts))

setup(
    name='tek',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    long_description='helper lib',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'crystalmethod',
        'tryp>=7.6.0'
    ],
)
