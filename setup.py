from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip()]

setup(
    name="puran_adm1",
    version="0.1.0",
    author="hvkshetry",
    author_email="hvkshetry@gmail.com",
    description="ADM1 Simulation App for anaerobic digestion modeling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hvkshetry/adm1-simulation-app",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "adm1-sim=app-refactored:main",
        ],
    },
)