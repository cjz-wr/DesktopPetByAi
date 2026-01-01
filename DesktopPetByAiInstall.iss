[Setup]
AppName=DesktopPetByAi
AppVersion=1.0
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
UninstallDisplayName=DesktopPetByAi
UninstallDisplayIcon={app}\DesktopPetByAi.exe

; 强制显示安装目录页面
DisableDirPage=no

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "D:\code\python\desktop_pet\main\DesktopPetByAi.exe"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件
Source: "D:\code\python\desktop_pet\main\*.json"; DestDir: "{app}"; Flags: ignoreversion 
; 资源文件夹
Source: "D:\code\python\desktop_pet\main\img\*"; DestDir: "{app}\img"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\code\python\desktop_pet\main\ico\*"; DestDir: "{app}\ico"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\code\python\desktop_pet\main\gif\*"; DestDir: "{app}\gif"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\code\python\desktop_pet\main\background\*"; DestDir: "{app}\background"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DesktopPetByAi"; Filename: "{app}\DesktopPetByAi.exe"
Name: "{userdesktop}\DesktopPetByAi"; Filename: "{app}\DesktopPetByAi.exe"; Tasks: desktopicon
; 卸载程序图标
Name: "{group}\卸载 DesktopPetByAi"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\DesktopPetByAi.exe"; Description: "启动 DesktopPetByAi"; Flags: nowait postinstall skipifsilent