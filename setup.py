from setuptools import setup, find_packages

setup(
    name="iris-core",
    version="0.1.0",
    description="Shared event contract for the IRIS incident intelligence ecosystem",
    author="Sai Sampath Ayalasomayajula",
    packages=find_packages(),
    package_data={"iris_core": ["schema.sql"]},
    python_requires=">=3.9",
    install_requires=[],
)