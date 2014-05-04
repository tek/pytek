
import glob

from setuptools import setup, find_packages

setup(name='tek',
      version='1.1.6',
      author='Torsten Schmits',
      author_email='torstenschmits@gmail.com',
      license='GPLv3',
      long_description='helper lib',
      packages=find_packages(exclude=['tests', 'scripts']),
      install_requires=['crystalmethod'],
      entry_points={
          'console_scripts': [
              'tek_write_config = tek.config.write:cli',
          ],
      }
      )
