FROM python:3.7 as pyinstaller

RUN mkdir -p /work
WORKDIR /work
ADD requirements.txt /work/
RUN pip install -r requirements.txt

ADD gmondflux /work/gmondflux
ADD gmondflux.spec /work/
ADD run.py /work/

RUN pyinstaller gmondflux.spec


FROM python:3.7 as upload

ARG SSH_KEY

ADD utils/sshconfig.py /sshconfig.py
RUN python3 /sshconfig.py

COPY --from=pyinstaller /work/dist/gmondflux /gmondflux

RUN scp /gmondflux droneagent@www.nerdworks.de:.
