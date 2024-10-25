
set -e # Exit if any command fails (particularly the first one)

./manage.py migrate gamedata zero
rm ./gamedata/migrations/0001_initial.py
./manage.py makemigrations
./manage.py migrate
git add ./gamedata/migrations/0001_initial.py
