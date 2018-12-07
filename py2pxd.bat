@echo off

set MDL=%1
if not ["%MDL%"] == [""] goto xeq_action

:prompt_user
set /P MDL=Fichier à traiter: 
goto xeq_action

:xeq_action
set PWD=%~dp0
@echo on
python %PWD%py2pxd.py -i %MDL%
pause
