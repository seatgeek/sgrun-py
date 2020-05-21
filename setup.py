from setuptools import setup, find_packages

setup(
    name="sgrun",
    version="0.0.1",
    packages=find_packages(),
    long_description=open("README.md").read(),
    install_requires=["ddtrace==0.37.1",],
    entry_points={"console_scripts": ["sgrun = sgrun.bootstrap.commandline:main"]},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
