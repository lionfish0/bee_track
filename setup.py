from distutils.core import setup
setup(
  name = 'bee_track',
  packages = ['bee_track'],
  version = '1.2',
  description = 'Runs the bee tracking system.',
  author = 'Mike Smith',
  author_email = 'm.t.smith@sheffield.ac.uk',
  url = 'https://github.com/lionfish0/bee_track.git',
  download_url = 'https://github.com/lionfish0/bee_track.git',
  keywords = ['bumblebees','ecology','tracking','retroreflectors'],
  classifiers = [],
  install_requires=['numpy'],
  scripts=['bin/btviewer'],
)
