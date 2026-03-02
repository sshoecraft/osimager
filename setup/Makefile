
all: tapthat

tapthat: tapthat.c
	cc -o tapthat tapthat.c

install: tapthat
	install -o bin -g bin tapthat /usr/local/sbin/tapthat

install_service::
	install -o root -g root -m 644 tapthat.service /etc/systemd/system/tapthat.service
	systemctl daemon-reload
	systemctl enable tapthat.service

clean:
	rm -f tapthat

adserver: infra.json Autounattend.xml
	packer build --only adserver infra.json

esxhost: infra.json ks.cfg
	packer build --only esxhost infra.json
