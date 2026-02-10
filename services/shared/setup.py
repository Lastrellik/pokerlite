"""Setup file for shared poker logic module."""
from setuptools import setup, find_packages

setup(
    name="pokerlite-shared",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "alembic>=1.13.0",
        "passlib[bcrypt]>=1.7.4",
        "bcrypt>=4.0.0,<5.0.0",  # Pin to 4.x due to passlib compatibility
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
    ],
)
