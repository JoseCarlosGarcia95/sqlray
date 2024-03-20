from setuptools import setup, find_packages

# Abre y lee los archivos necesarios
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="sqlray",
    version="0.1.1",
    author="Jose Carlos Garcia Ortega",
    author_email="hola@josecarlos.me",
    description="SQLRay is a tool that helps you optimize SQL queries using OpenAI.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://tu-url-del-proyecto.com",
    project_urls={
        "Bug Tracker": "https://tu-url-del-proyecto.com/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "sqlray"},
    packages=find_packages(where="sqlray"), 
    python_requires=">=3.6",
    install_requires=requirements, 
    entry_points={
        "console_scripts": [
            "sqlray=app:cli",  
        ],
    },
    include_package_data=True,
)
