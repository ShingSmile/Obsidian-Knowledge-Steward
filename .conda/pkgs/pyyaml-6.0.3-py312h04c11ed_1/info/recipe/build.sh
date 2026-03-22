#!/bin/bash -eux

if [[ "$use_noarch" == "true" ]]; then
  export PYYAML_FORCE_LIBYAML=0
fi
${PYTHON} -m pip install . --no-deps --no-build-isolation -vv
