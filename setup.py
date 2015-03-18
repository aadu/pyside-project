# Always prefer setuptools over distutils
from setuptools import setup, find_packages

install_requires = [
    'PySide>=1.0.7',
    'numpy>=1.9.0',
    'pandas>=0.15.0',
    'formencode',
    'yaml']

setup(
    name='surveyor',
    version='0.0.1',
    description='Process surveys',
    url='https://github.com/aadu/pyside-project',
    author='Aaron Duke',
    author_email='aaron.duke@outlook.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'
    ],
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=install_requires,
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage', 'pytest'],
    }
)
