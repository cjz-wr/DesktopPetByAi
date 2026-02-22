[Setup]
AppName=DesktopPetByAi
AppVersion=2.1.7
DefaultDirName={userpf}\DesktopPetByAi
DefaultGroupName=DesktopPetByAi
OutputDir=Output
OutputBaseFilename=DesktopPetByAi
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

; 卸载程序设置
CreateUninstallRegKey=yes
Uninstallable=yes
UninstallDisplayName=UNinstallDesktopPetByAi
UninstallDisplayIcon={app}\DesktopPetByAi.exe

; 强制显示安装目录页面
DisableDirPage=no

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\DesktopPetByAi.exe"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件(检查中)
; Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\*.json"; DestDir: "{app}"; Flags: ignoreversion 
; 资源文件夹
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\imgs\*"; DestDir: "{app}\imgs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\ico\*"; DestDir: "{app}\ico"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\gif\*"; DestDir: "{app}\gif"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\background\*"; DestDir: "{app}\background"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\imgs\*"; DestDir: "{app}\background"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\outfood\*"; DestDir: "{app}\outfood"; Flags: ignoreversion recursesubdirs createallsubdirs
;资源文件
Source: "C:\Users\CJZ\Desktop\update\DesktopPetByAi\DesktopPetByAi\log.yaml"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DesktopPetByAi"; Filename: "{app}\DesktopPetByAi.exe"
Name: "{userdesktop}\DesktopPetByAi"; Filename: "{app}\DesktopPetByAi.exe"; Tasks: desktopicon
; 卸载程序图标
Name: "{group}\卸载 DesktopPetByAi"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\DesktopPetByAi.exe"; Description: "启动 DesktopPetByAi"; Flags: nowait postinstall skipifsilent