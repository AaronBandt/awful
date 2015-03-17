import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGELOG.rst')) as f:
    CHANGELOG = f.read()

requires = [
    'pyramid==1.5.1',
    'pyramid_chameleon==0.3',
    'pyramid_debugtoolbar==2.2',
    'pyramid-tm==0.7',
    'pyramid-mako==1.0.2',
    'Pygments==1.6',
    'waitress==0.8.9',
    'SQLAlchemy==0.9.7',
    'mysql-connector-python==1.2.3',
    'transaction==1.4.3',
    'zope.sqlalchemy==0.7.5',
    'requests==2.3.0',
    'arrow==0.4.4',
    'passlib==1.6.2',
    ]

setup(name='awfulweb',
      version='0.1',
      description='Awful web api/ui',
      long_description=README + '\n\n' + CHANGELOG,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Aaron Bandt',
      author_email='aaron.bandt@citygridmedia.com',
      url='',
      license='Apache',
      keywords='Awful devops',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      dependency_links = ['http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-1.2.3.zip#md5=6d42998cfec6e85b902d4ffa5a35ce86'],
      tests_require=requires,
      test_suite="awfulweb",
      entry_points="""\
      [paste.app_factory]
      main = awfulweb:main
      [console_scripts]
      initialize_awful-web_db = awfulweb.scripts.initializedb:main
      """,
      )
