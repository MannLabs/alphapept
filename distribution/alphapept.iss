[Setup]
AppName=AlphaPept
AppPublisher=Mann Labs
AppVersion=0.2.9-dev0
DefaultDirName={commonpf}\AlphaPept
DefaultGroupName=AlphaPept
OutputBaseFilename="AlphaPept-Windows-64bit-0.2.9-dev0"
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\\alphapept\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Search"; Filename: "{app}\alphapeptw.exe"; Parameters: "gui"; IconFilename: "{app}\alphapept\gui\img\logo.ico"
Name: "{commondesktop}\AlphaPept"; Filename: "{app}\alphapeptw.exe"; Parameters: "gui"; IconFilename: "{app}\alphapept\gui\img\logo.ico"

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; \
    Check: NeedsAddPath('{app}')

[Code]

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
  ParamExpanded: string;
begin
  //expand the setup constants like {app} from Param
  ParamExpanded := ExpandConstant(Param);
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  // look for the path with leading and trailing semicolon and with or without \ ending
  // Pos() returns 0 if not found
  Result := Pos(';' + UpperCase(ParamExpanded) + ';', ';' + UpperCase(OrigPath) + ';') = 0;
  if Result = True then
     Result := Pos(';' + UpperCase(ParamExpanded) + '\;', ';' + UpperCase(OrigPath) + ';') = 0;
end;
