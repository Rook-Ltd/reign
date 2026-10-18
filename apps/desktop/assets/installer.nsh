; Included by electron-builder's NSIS template (build.nsis.include).
;
; Reign installs per-user only, so a non-admin can install it without UAC.
; With oneClick=false and perMachine=false the stock assisted installer still
; offers "Anyone who uses this computer", and picking it (or a leftover
; per-machine install making it the default) re-launches the installer
; elevated. Force the per-user mode so that page and its elevation never run.
!macro customInstallMode
  StrCpy $isForceCurrentInstall "1"
!macroend
