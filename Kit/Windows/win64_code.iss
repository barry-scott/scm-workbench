function InitializeUninstall(): Boolean;
  var ErrorCode: Integer;
begin
  ShellExec('open','taskkill.exe','/f /im "%(app_id)s.exe"','',SW_HIDE,ewNoWait,ErrorCode);
  ShellExec('open','tskill.exe',' "%(app_id)s"','',SW_HIDE,ewNoWait,ErrorCode);
  result := True;
end;

procedure UninstallOldVersions( root_key : Integer );
var
    uninstall_image     : string;
    error               : Integer;
    rci                 : Integer;
    rcb                 : Boolean;
begin
    error := 0;
    rcb := RegQueryStringValue( root_key,
        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(app_id)s_is1',
        'UninstallString', uninstall_image );
    if rcb then
    begin
        rci := MsgBox( 'An old version of %(app_id)s is installed.' #13 #13
                       'It must be uninstalled before installing the this version' #13
                       'Do you wish to uninstall it now?', mbConfirmation, MB_YESNO );
        if rci = idYes then
        begin
            InitializeUninstall();
            rcb := Exec( RemoveQuotes( uninstall_image ), '',
                            ExpandConstant('{src}'), SW_SHOWNORMAL, ewWaitUntilTerminated, Error );
            if not rcb then
                MsgBox( 'Failed to run the uninstall procedure.' #13 #13
                        'Please uninstall the old SCM Workbench' #13
                        'and try this installation again.', mbError, MB_OK );
            if error <> 0 then
                MsgBox( 'Failed to run the uninstall procedure.' #13 #13
                        'Please uninstall the old SCM Workbench' #13
                        'and try this installation again.', mbError, MB_OK );
        end;
    end;
end;

function InitializeSetup() : Boolean;
var
    uninstall_string    : string;
    rc32                : Boolean;
    rc64                : Boolean;
begin
    UninstallOldVersions( HKLM32 );
    UninstallOldVersions( HKLM64 );

    BringToFrontAndRestore;
    rc32 := RegQueryStringValue( HKLM32,
        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(app_id)s_is1',
        'UninstallString', uninstall_string );
    rc64 := RegQueryStringValue( HKLM64,
        'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(app_id)s_is1',
        'UninstallString', uninstall_string );
    Result := not (rc32 or rc64);
    if not Result then
        MsgBox( 'Quitting installation.' #13 #13
                'An old version of %(app_id)s is still installed.' #13
                'Run this installation again after the old version has' #13
                'been uninstalled', mbInformation, MB_OK );
end;
