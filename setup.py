"""
Setup configuration for fastapi-timeout package.
"""

from setuptools import setup, find_packages

setup(
    name="fastapi-timeout",
    use_scm_version=False,
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    python_requires=">=3.7",
    package_data={
        "fastapi_timeout": ["py.typed"],
    },
    zip_safe=False,
)
