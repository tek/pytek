from setuptools import setup, find_packages

setup(name='tek',
      version='1.1.7',
      author='Torsten Schmits',
      author_email='torstenschmits@gmail.com',
      license='GPLv3',
      long_description='helper lib',
      packages=find_packages(exclude=['tests', 'tests.*']),
      install_requires=['crystalmethod'],
      )
