@echo off
title requirement installer
py -3 -m pip install git+https://github.com/dolfies/discord.py-self@renamed#egg=selfcord.py[voice]
pip install openai
pip install -U g4f
echo requirements were downloaded successfully!
pause
