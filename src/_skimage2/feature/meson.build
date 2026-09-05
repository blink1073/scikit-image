pyx_files = [
  ['corner_cy', cython_gen],
  ['censure_cy', cython_gen],
  ['orb_cy', cython_gen],
  ['_texture', cython_gen],
  ['_hoghistogram', cython_gen],
  ['_sift', cython_gen],
  ['_cascade', cython_gen_cpp],
  ['_haar', cython_gen_cpp],
  ['_canny_cy', cython_gen],
  ['brief_cy', cython_gen],
  ['_hessian_det_appx', cython_gen],
]

foreach pyx_file: pyx_files
  py3.extension_module(pyx_file[0],
    pyx_file[1].process(pyx_file[0] + '.pyx'),
    c_args: cython_c_args,
    cpp_args: cython_cpp_args,
    include_directories: ['../../_skimage2/_shared'],
    dependencies: [np_dep],
    limited_api: limited_api_ver,
    install: true,
    subdir: '_skimage2/feature'
  )
endforeach

python_sources = [
  '__init__.py',
  '__init__.pyi',
  '_basic_features.py',
  '_canny.py',
  '_daisy.py',
  '_hog.py',
  '_orb_descriptor_positions.py',
  'blob.py',
  'brief.py',
  'censure.py',
  'corner.py',
  '_fisher_vector.py',
  'haar.py',
  'match.py',
  'orb.py',
  '_peaks.py',
  'sift.py',
  'template.py',
  'texture.py',
  'util.py',
]

py3.install_sources(
  python_sources,
  pure: false,             # Will be installed next to binaries
  subdir: '_skimage2/feature'  # Folder relative to site-packages to install to
)

py3.install_sources(
  ['orb_descriptor_positions.txt'],
  pure: false,             # Will be installed next to binaries
  subdir: '_skimage2/feature'  # Folder relative to site-packages to install to
)
