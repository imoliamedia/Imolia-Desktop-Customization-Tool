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
    url="https://github.com/ImolaMedia/desktop-customization-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
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