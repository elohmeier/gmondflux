venv: env.nix
	nix-build env.nix -o venv

.PHONY: black
black:
	black gmondflux
	black tests

.PHONY: flake8
flake8:
	nix-shell -p python2Packages.flake8 --run "flake8 --ignore E501 src"

.PHONY: upload
upload:
	scp -r dist/* nw32.nw:/var/www/nerdworks.de/prod/aix/

.PHONY: pdkimg
pdkimg: pdkenv/Dockerfile.pdk
	docker build -t pdkenv -f pdkenv/Dockerfile.pdk pdkenv

.PHONY: puppetimg
puppetimg: pdkenv/Dockerfile.puppet
	docker build -t puppetenv -f pdkenv/Dockerfile.puppet pdkenv

.PHONY: pdk
pdk: pdkimg
	docker run -it --rm -v $(shell pwd):/work pdkenv bash

.PHONY: puppet
puppet: puppetimg
	docker run -it --rm -v $(shell pwd)/puppet/gmond2influx:/etc/puppetlabs/code/modules/gmond2influx puppetenv bash

.PHONY: validate
validate: pdkimg
	docker run -it --rm -v $(shell pwd)/puppet/gmond2influx:/work pdkenv pdk validate

#apply: puppetimg
#	docker run -it --rm -v $(shell pwd)/puppet/gmond2influx:/etc/puppetlabs/code/modules/gmond2influx puppetenv /opt/puppetlabs/bin/puppet apply gmond2influx/manifests/site.pp

.PHONY: apply
apply:
	sudo /opt/puppetlabs/bin/puppet apply --modulepath puppet/ -e 'include gmond2influx' --test

.PHONY: docker
docker:
	docker build -t gmondflux --target pyinstaller .

.PHONY: dockerdist
dockerdist: docker
	mkdir -p dist
	rm -f dist/gmondflux
	docker run --rm --entrypoint cat gmondflux /work/dist/gmondflux > dist/gmondflux


