"""Legacy shim for setuptools/PEP 517 builds.

Primary package metadata now lives in pyproject.toml.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()

