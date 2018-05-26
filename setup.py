from setuptools import setup, find_packages

setup(
    name='django-beam',
    version='0.0.1',
    url='https://github.com/django-beam/django-beam',
    download_url='https://github.com/django-beam/django-beam/archive/0.0.1.tar.gz',
    description='A workflow library for python',
    packages=find_packages(),
    author='Raphael Kimmig',
    author_email='raphael@ampad.de',
    install_requires=['django >= 1.11', ],
)
