from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = fh.read()

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sqlray",
    version="1.0.0",
    author="Jose Carlos Garcia Ortega",
    author_email="hola@josecarlos.me",
    description="SQLRay is a tool that helps you optimize SQL queries using OpenAI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JoseCarlosGarcia95/sqlray",
    project_urls={
        "Bug Tracker": "https://github.com/JoseCarlosGarcia95/sqlray/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),  
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "sqlray=sqlray.app:cli",  
        ],
    },
    include_package_data=True,
)
