all:
	docker build -t b00bl1k/avbot .
	docker push b00bl1k/avbot

messages:
	pybabel extract -k __ --input-dirs=avbot -o avbot/locale/avbot.po
	pybabel update -d avbot/locale -D avbot -i avbot/locale/avbot.po
