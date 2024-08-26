# Use an official Python image as a base
FROM python:3.12

# Set the working directory to /snatch
WORKDIR /snatch

RUN apt update && apt install tor xvfb xfce4 xfce4-goodies tightvncserver net-tools curl openssh-server dbus-x11 -y

# install chrom
RUN apt install firefox-esr -y

# install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz && tar -xzf geckodriver-v0.34.0-linux-aarch64.tar.gz && mv geckodriver /usr/local/bin/

# Install Python dependencies
COPY . /snatch/
RUN pip install -e .

# service tor start
# Xvfb :1 -screen 0 1024x768x16 &
# export DISPLAY=:1
# RUN Xvfb -nolisten tcp :1 & echo $? > display.pid
# service tor status
# ps -ef | grep Xvfb

ENTRYPOINT [ "snatch" ]