# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in unrestrict_erpnext/__init__.py
from biometric_attendance import __version__ as version

setup(
	name='biometric_attendance',
	version=version,
	description='Integrates Biometric Device Attendance',
	author='Akshay Mehta',
	author_email='mehta.akshay@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
