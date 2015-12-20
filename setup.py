from setuptools import setup, find_packages

setup(name='tek',
      version='1.1.8',
      author='Torsten Schmits',
      author_email='torstenschmits@gmail.com',
      license='MIT',
      long_description='helper lib',
      packages=find_packages(exclude=['tests', 'tests.*']),
      install_requires=['crystalmethod'],
      )
