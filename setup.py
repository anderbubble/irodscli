import setuptools
setuptools.setup(
    name="irodscli",
    version="0.0.0",
    description="An iRODS CLI based on python-irodsclient",
    packages=setuptools.find_packages(
        where="src",
    ),
    package_dir={"": "src"},
    install_requires=[
        'python-irodsclient',
    ],
    entry_points={
        'console_scripts': [
            'irods = irodscli.main:main',
        ],
    }
)
