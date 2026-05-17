; Jury Selection Tool — Inno Setup installer script
; Compile with Inno Setup 6+ (https://jrsoftware.org/isdl.php)

[Setup]
AppId={{A3F2C1D8-7B4E-4F9A-B562-1E3D8C0A5F72}
AppName=Jury Selection Tool
AppVersion=1.0.3
AppPublisher=Cole Mason
AppPublisherURL=
DefaultDirName={localappdata}\Programs\JuryTool
DefaultGroupName=Jury Selection Tool
OutputBaseFilename=JuryTool_Setup
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
Source: "dist\JuryTool\JuryTool.exe"; DestDir: "{app}"; Flags: ignoreversion
; All bundled dependencies
Source: "dist\JuryTool\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Jury Selection Tool"; Filename: "{app}\JuryTool.exe"
Name: "{group}\Uninstall Jury Selection Tool"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Jury Selection Tool"; Filename: "{app}\JuryTool.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\JuryTool.exe"; Description: "Launch Jury Selection Tool"; Flags: nowait postinstall skipifsilent

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A3F2C1D8-7B4E-4F9A-B562-1E3D8C0A5F72}_is1';
  sUnInstallString := '';
  if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    sUnInstallString := GetUninstallString();
    if sUnInstallString <> '' then
      Exec(RemoveQuotes(sUnInstallString), '/SILENT /NORESTART /SUPPRESSMSGBOXES',
           '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  end;
end;
