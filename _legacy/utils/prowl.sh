#!/bin/sh

curl https://api.prowlapp.com/publicapi/add -F apikey="$PROWL_APIKEY" -F application="$DRONE_REPO" -F event="build #$DRONE_BUILD_NUMBER" -F description="$*"
