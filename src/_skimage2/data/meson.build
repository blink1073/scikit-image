python_sources = [
  '__init__.py',
  '__init__.pyi',
  '_synthetic.py',
  '_fetchers.py',
  '_registry.py',
]

py3.install_sources(
  python_sources,
  pure: false,             # Will be installed next to binaries
  subdir: '_skimage2/data'  # Folder relative to site-packages to install to
)

py3.install_sources(
  ['README.txt'],
  pure: false,
  subdir: '_skimage2/data'
)
