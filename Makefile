messages:
	pybabel extract -k __ --input-dirs=avbot -o avbot/locale/avbot.po
	pybabel update -d avbot/locale -D avbot -i avbot/locale/avbot.po

compilemessages:
	pybabel compile -d avbot/locale -D avbot
