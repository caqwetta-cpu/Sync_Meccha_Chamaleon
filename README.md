# Sync_Meccha_Chamaleon
Sincronizzazione cartella workshop dei contenuti di Meccha Chamaleon nella cartella del gioco stesso.


Requisiti:

1) Mappe del gioco scaricati direttamente dal workshop. 
es. Z:\SteamLibrary\steamapps\workshop\content\4704690
2) Gioco nella cartella originale di steam.
es. Z:\SteamLibrary\steamapps\common\MECCHA CHAMELEON
3) C'è il bisogno del "OnlineFix.ini" dentro "...\MECCHA CHAMELEON\Chameleon\Binaries\Win64"


Funzionamento: dentro "...\MECCHA CHAMELEON\Chameleon\Binaries\Win64", viene creata una cartella chiamata "workshop".
Poi vengono sincronizzati i contenuti della cartella "...\steamapps\workshop\content\4704690" e la cartella "...\MECCHA CHAMELEON\Chameleon\Binaries\Win64\workshop", se ci sono mappe scricate.
