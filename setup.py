from setuptools import setup, find_packages

setup(
    name="pyzdata",
    version="0.1.0",
    description="Historical data downloader using Zerodha API",
    author="Vikas Sharma",
    author_email="Jnv2252@Gmail.com",
    url="https://github.com/vikassharma545/Historical-Market-data-From-Zerodha",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "requests>=2.0.0",
        "urllib3>=1.25.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
)
