#! /bin/sh

echo "Updating compressed packages for distribution"
cd src
tar czvf xatfanjac.tar.gz *.py
zip xatfanjac.zip *.py
mv xatfanjac.zip xatfanjac.tar.gz ../dist

