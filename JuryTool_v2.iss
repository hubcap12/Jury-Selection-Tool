; Jury Selection Tool v2 — Inno Setup installer script
; Compile with Inno Setup 6+ (https://jrsoftware.org/isdl.php)

[Setup]
AppId={{B7E4D2F1-9C3A-4E8B-A671-2F5E9D1B6C83}
AppName=Jury Selection Tool
AppVersion=2.0.4
AppPublisher=Cole Mason
AppPublisherURL=
DefaultDirName={localappdata}\Programs\JuryTool
DefaultGroupName=Jury Selection Tool
OutputBaseFilename=JuryTool_v2_Setup
SetupIconFile=icon.ico
OutputDir=installer
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main executable
Source: "dist\JuryTool_v2\JuryTool_v2.exe"; DestDir: "{app}"; Flags: ignoreversion
; All bundled dependencies
Source: "dist\JuryTool_v2\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Jury Selection Tool"; Filename: "{app}\JuryTool_v2.exe"
Name: "{group}\Uninstall Jury Selection Tool"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Jury Selection Tool"; Filename: "{app}\JuryTool_v2.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\JuryTool_v2.exe"; Description: "Launch Jury Selection Tool"; Flags: nowait postinstall skipifsilent

[Code]
function GetUninstallStringFor(const AppGuid: String): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{' + AppGuid + '}_is1';
  sUnInstallString := '';
  if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

procedure UninstallPrior(const AppGuid: String);
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  sUnInstallString := GetUninstallStringFor(AppGuid);
  if sUnInstallString <> '' then
    Exec(RemoveQuotes(sUnInstallString), '/SILENT /NORESTART /SUPPRESSMSGBOXES',
         '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    { Silently uninstall any previous v2 build }
    UninstallPrior('B7E4D2F1-9C3A-4E8B-A671-2F5E9D1B6C83');
    { ...and any v1 build (the Tkinter installer used a different AppId) }
    UninstallPrior('A3F2C1D8-7B4E-4F9A-B562-1E3D8C0A5F72');
  end;
end;
