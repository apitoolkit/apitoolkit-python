from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="apitoolkit-python",
    version="0.1.3",
    packages=find_packages(),
    description='A share python sdk for python web frameworks',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email='hello@apitoolkit.io',
    author='APIToolkit',
    install_requires=[
        'requests',
        'httpx',
        'jsonpath-ng',
    ],
)
