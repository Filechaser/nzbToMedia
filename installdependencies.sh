#!/usr/bin/env bash
pip install -U pip setuptools
pip install requests
pip install requests[security]
pip install requests-cache
pip install babelfish
pip install "guessit<2"
pip install "subliminal<2"
pip uninstall stevedore --y
pip install stevedore==1.19.1
pip install python-dateutil
pip install deluge-client
pip install qtfaststart
pip install beets