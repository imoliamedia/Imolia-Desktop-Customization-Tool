# Copyright (C) 2024 Imolia Media
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="desktop-customization-tool",
    version="0.1.0",
    author="Imolia Media",
    author_email="contact@imoliamedia.com",
    description="A customizable desktop overlay tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/imoliamedia/Imolia-Desktop-Customization-Tool.git",
    packages=find_packages(),
    license="GNU General Public License v3.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "PyQt5>=5.15.0",
    ],
    entry_points={
        "console_scripts": [
            "desktop-customizer=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["resources/*"],
    },
)