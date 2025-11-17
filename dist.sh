#!/bin/bash

# if [ $# -ne 1 ]; then
# 	echo "dist.sh: Wrong number of arguments"
# 	echo "Usage: dist.sh *tag*"
# 	exit 2
# fi

TAG=$(git describe --tags --abbrev=0)
BASE_NAME="dr-mentions"
DIR_NAME="$BASE_NAME"
TAR_NAME="$BASE_NAME-$TAG.tgz"
FILES="dr-mentiond dr-mentiond.service dr-mentions.conf \
	dr-mentions.py config.py \
	install.sh uninstall.sh dist.sh \
	icon.png README.md requirements.txt"

set -e
echo "Generating $TAR_NAME..."
mkdir $DIR_NAME
cp -r $FILES $DIR_NAME/
tar -cvzf $TAR_NAME $DIR_NAME
rm -r $DIR_NAME
echo "Done!"
