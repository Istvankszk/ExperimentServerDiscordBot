#!/bin/bash
#Purpose = Start and keep alive sigma discord bot
#Created on 15/03/2018
#Author = IstvanKSZK
#Version 1.0

cd ~/SigmaDiscordBot/
until ~/Python-3.6.4/python SigmaDiscordBot.py > log.txt 2>&1; do #requires python 3.6 on linux
	mv log.txt log-$`date "+%F-%H-%M"`.txt
	sleep 1
done