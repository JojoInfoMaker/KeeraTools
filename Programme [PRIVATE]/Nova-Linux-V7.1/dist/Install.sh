chmod +x AppV7.x86_64

sudo cp -i AppV7.x86_64 ~/.local/bin

touch Nova-Installer.desktop
echo [Desktop Entry] >> Nova-Installer.desktop
echo Name="Nova Installer" >> Nova-Installer.desktop
echo Exec=~/.local/bin/AppV7.x86_64 >> Nova-Installer.desktop
echo Icon=NOTDEFINED >> Nova-Installer.desktop
echo Type=Application >> Nova-Installer.desktop
echo Terminal=false >> Nova-Installer.desktop

mv Nova-Installer.desktop /home/$USER/Desktop
