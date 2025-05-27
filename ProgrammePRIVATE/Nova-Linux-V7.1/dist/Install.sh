chmod +x AppV7.x86_64 #autorise AppV7.x86_64 à être éxécuté en double clique

sudo cp -i AppV7.x86_64 ~/.local/bin #bouge AppV7.x86_64 dans /home/$USER/.local/bin (pour que le .desktop trouve super vite et universelement)

mkdir ~/.local/share/icons/Nova-Installer #créer un dossier pour les icones
cd data
cp inco.png ~/.local/share/icons/Nova-Installer #bouge l'icone dans le bon dossier
cd -

touch Nova-Installer.desktop
echo [Desktop Entry] >> Nova-Installer.desktop
echo Name="Nova Installer" >> Nova-Installer.desktop
echo Exec=~/.local/bin/AppV7.x86_64 >> Nova-Installer.desktop
echo Icon=~/.local/share/icons/Nova-Installer/inco.png >> Nova-Installer.desktop #s'occupe de créer d'écrire dans le .desktop
echo Type=Application >> Nova-Installer.desktop
echo Terminal=false >> Nova-Installer.desktop
chmod +x Nova-Installer.desktop

mv Nova-Installer.desktop ~/.local/share/applications #bouge sur le Bureau le .desktop
