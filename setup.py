from setuptools import find_packages, setup

setup(
    name='main_flask_app',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'pandas',
        'geopandas',
        'openpyxl',
        'flask==2.2.3',
        'flask_sqlalchemy',
        'flask_wtf',
        'wtforms',
        'flask_login',
        'passlib',
        'flask_marshmallow',
        'marshmallow-sqlalchemy',
        'pathlib',
        'dash_bootstrap_components',
        'dash',
        'plotly.express',
        'numpy',
        'pyproj',
        'area',
        'requests',
        'pytest',
        'pytest-flask',
        'selenium',
        'pytest-cov',
        'flask-testing'  
    ],
)
