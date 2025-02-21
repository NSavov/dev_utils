from setuptools import find_packages, setup

setup(
    name="dev_utils",
    version="0.3.0",
    author="Nedko Savov",
    author_email="nedko.savov@insait.ai",
    description="Common tools I use for development",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/NSavov/dev_utils",
    packages=find_packages(),
    install_requires=[
        "natsort",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
