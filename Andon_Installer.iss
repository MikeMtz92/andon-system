; Script Inno Setup para ReAction Andon System
; Guardar como: Andon_Installer.iss

[Setup]
AppName=ReAction Andon System
AppVersion=2.1
AppPublisher=Monsterweb
AppPublisherURL=https://monsterweb.com.mx
AppSupportURL=https://monsterweb.com.mx
AppUpdatesURL=https://monsterweb.com.mx
DefaultDirName={pf}\ReAction Andon System
DefaultGroupName=ReAction Andon System
UninstallDisplayIcon={app}\ReActionAndon.exe
UninstallDisplayName=ReAction Andon System
Compression=lzma2/ultra
SolidCompression=yes
OutputDir=Instalador_Final
OutputBaseFilename=ReActionAndon_Setup_v2.1
SetupIconFile=recursos\icono.ico
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "quicklaunchicon"; Description: "Crear acceso directo en inicio rápido"; GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "autostart"; Description: "Iniciar con Windows"; GroupDescription: "Opciones de inicio:"; Flags: unchecked

[Files]
; Ejecutable principal
Source: "instalador\ReActionAndon.exe"; DestDir: "{app}"; Flags: ignoreversion

; Recursos
Source: "recursos\icono.ico"; DestDir: "{app}"; Flags: ignoreversion

; Carpeta para sonidos personalizados (opcional)
Source: "recursos\sounds\*"; DestDir: "{app}\sounds"; Flags: ignoreversion recursesubdirs createallsubdirs

; README
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\ReAction Andon System"; Filename: "{app}\ReActionAndon.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icono.ico"
Name: "{group}\Desinstalar ReAction Andon"; Filename: "{uninstallexe}"; IconFilename: "{app}\icono.ico"
Name: "{autodesktop}\ReAction Andon System"; Filename: "{app}\ReActionAndon.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icono.ico"; Tasks: desktopicon
Name: "{userstartup}\ReAction Andon System"; Filename: "{app}\ReActionAndon.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icono.ico"; Tasks: autostart

[Run]
Filename: "{app}\ReActionAndon.exe"; Description: "Ejecutar ReAction Andon System ahora"; Flags: postinstall nowait skipifsilent
Filename: "{app}"; Description: "Abrir carpeta de instalación"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallRun]
Filename: "{cmd}"; Parameters: "/c if exist ""{app}\db_config.json"" del ""{app}\db_config.json"""; Flags: runhidden; RunOnceId: "CleanConfig"
Filename: "{cmd}"; Parameters: "/c if exist ""{app}\sounds"" rmdir /s /q ""{app}\sounds"""; Flags: runhidden; RunOnceId: "CleanSounds"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssDone then
  begin
    MsgBox('¡Instalación completada con éxito!' + #13#10 + #13#10 +
           'ReAction Andon System v2.1 ha sido instalado correctamente.' + #13#10 + #13#10 +
           'NOVEDADES v2.1:' + #13#10 +
           '• Sonidos personalizados por tipo de falla (licencia PRO)' + #13#10 +
           '• Soporte para torreta de colores en botonera ESP32' + #13#10 +
           '• Mejoras en rendimiento y estabilidad' + #13#10 + #13#10 +
           'IMPORTANTE:' + #13#10 +
           '• Al ejecutar el programa por primera vez, se te pedirá activar una licencia' + #13#10 +
           '• Luego deberás configurar la conexión a MySQL' + #13#10 +
           '• Los sonidos personalizados se guardan en la carpeta sounds' + #13#10 + #13#10 +
           '¡Gracias por elegir ReAction Andon System!', 
           mbInformation, MB_OK);
  end;
end;