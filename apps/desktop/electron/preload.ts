import { contextBridge, ipcRenderer, webFrame, webUtils } from 'electron'

// Which translucency the OS can back. Asked synchronously because the renderer
// needs it before its first paint, and answered by main because deciding it
// needs `os.release()` — a sandboxed preload may only require electron, events,
// timers and url, so importing node:os here throws before contextBridge runs
// and takes the ENTIRE bridge down with it (window.reignDesktop undefined =>
// "Desktop IPC bridge is unavailable"). No reply means no glass, which degrades
// to an ordinary opaque window rather than a page thinned over nothing.
const translucencySupport = ipcRenderer.sendSync('reign:translucency:support')
const hudWindowing = ipcRenderer.sendSync('reign:hud:windowing')
const hudNativeDrag = hudWindowing?.nativeDrag === true
const launchFlags = ipcRenderer.sendSync('reign:launch-flags')

contextBridge.exposeInMainWorld('reignDesktop', {
  glassSupported: translucencySupport?.glass === true,
  translucencySupported: translucencySupport?.translucency === true,
  // Launch-flag fact: the app was started with --local, so the renderer may
  // show the local-models surfaces. Static for the window's lifetime.
  localModelsEnabled: launchFlags?.localModels === true,
  getConnection: profile => ipcRenderer.invoke('reign:connection', profile),
  // Registry-scoped backend resolution: { connectionId, profile } → descriptor.
  getConnectionFor: payload => ipcRenderer.invoke('reign:connection:for', payload),
  getProfileRoutes: profiles => ipcRenderer.invoke('reign:plugin-profile-routes', profiles),
  revalidateConnection: () => ipcRenderer.invoke('reign:connection:revalidate'),
  touchBackend: profile => ipcRenderer.invoke('reign:backend:touch', profile),
  getGatewayWsUrl: profile => ipcRenderer.invoke('reign:gateway:ws-url', profile),
  // Registry-scoped fresh WS URL: { connectionId, profile } → result shape of
  // getGatewayWsUrl, minted against that connection's backend.
  getGatewayWsUrlFor: payload => ipcRenderer.invoke('reign:gateway:ws-url-for', payload),
  // Union agent roster across every registered connection.
  getAgentRoster: () => ipcRenderer.invoke('reign:agents:roster'),
  openSessionWindow: (sessionId, opts) => ipcRenderer.invoke('reign:window:openSession', sessionId, opts),
  openSessionInTerminal: (sessionId, opts) => ipcRenderer.invoke('reign:window:openInTerminal', sessionId, opts),
  openWindow: () => ipcRenderer.invoke('reign:window:openInstance'),
  openBrowserWindow: tabId => ipcRenderer.invoke('reign:window:openBrowser', tabId),
  onBrowserPopoutClosed: callback => {
    const listener = (_event, tabId) => callback(tabId)
    ipcRenderer.on('reign:browser-popout:closed', listener)

    return () => ipcRenderer.removeListener('reign:browser-popout:closed', listener)
  },
  claimAmbientCue: key => ipcRenderer.invoke('reign:ambient:claim', key),
  wakeIndicator: {
    getState: () => ipcRenderer.invoke('reign:wake-indicator:get'),
    setState: state => ipcRenderer.send('reign:wake-indicator:set', state),
    onState: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('reign:wake-indicator:state', listener)

      return () => ipcRenderer.removeListener('reign:wake-indicator:state', listener)
    }
  },
  petOverlay: {
    // Main renderer → main process: window lifecycle + drag. `request` is
    // `{ bounds, screen }`; resolves with the screen bounds it actually used.
    open: request => ipcRenderer.invoke('reign:pet-overlay:open', request),
    close: () => ipcRenderer.invoke('reign:pet-overlay:close'),
    setBounds: bounds => ipcRenderer.send('reign:pet-overlay:set-bounds', bounds),
    setIgnoreMouse: ignore => ipcRenderer.send('reign:pet-overlay:ignore-mouse', ignore),
    // Flip the overlay focusable (and focus it) while the composer needs keys.
    setFocusable: focusable => ipcRenderer.send('reign:pet-overlay:set-focusable', focusable),
    // Main renderer → overlay (forwarded by main): push the latest pet state.
    pushState: payload => ipcRenderer.send('reign:pet-overlay:state', payload),
    // Overlay → main renderer (forwarded by main): pop back in / composer submit.
    control: payload => ipcRenderer.send('reign:pet-overlay:control', payload),
    // Overlay subscribes to state pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:pet-overlay:state', listener)

      return () => ipcRenderer.removeListener('reign:pet-overlay:state', listener)
    },
    // Main renderer subscribes to overlay control messages.
    onControl: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:pet-overlay:control', listener)

      return () => ipcRenderer.removeListener('reign:pet-overlay:control', listener)
    }
  },
  // HUD mode: the chrome-free floating chat. A full app renderer (own gateway)
  // sized as a floating bar, so it mounts the real composer. Main owns the
  // window; `onChanged` keeps every window's toggle truthful.
  hud: {
    nativeDrag: hudNativeDrag,
    windowing: {
      clientPlacement: hudWindowing?.clientPlacement !== false,
      controlDrag: hudWindowing?.controlDrag === true,
      nativeDrag: hudNativeDrag,
      solid: hudWindowing?.solid === true,
      workspaceTransfer: hudWindowing?.workspaceTransfer === true
    },
    open: request => ipcRenderer.invoke('reign:hud:open', request),
    close: () => ipcRenderer.invoke('reign:hud:close'),
    setIgnoreMouse: ignore => ipcRenderer.send('reign:hud:ignore-mouse', ignore),
    beginMove: () => ipcRenderer.send('reign:hud:begin-move'),
    endMove: () => ipcRenderer.send('reign:hud:end-move'),
    moveBy: delta => ipcRenderer.send('reign:hud:move-by', delta),
    setWorkspaceTransfer: transferring => ipcRenderer.send('reign:hud:workspace-transfer', transferring),
    setBounds: bounds => ipcRenderer.send('reign:hud:set-bounds', bounds),
    resetLayout: () => ipcRenderer.invoke('reign:hud:reset-layout'),
    // Whether the band covers the window below the bar. Main pairs it with the
    // user's translucency setting to decide the native frost (macOS vibrancy /
    // Windows 11 DWM backdrop) — see hudFrostFor.
    setFrost: showing => ipcRenderer.invoke('reign:hud:frost', showing),
    // The HUD tells main which session it is on; main hands that back to the
    // app window when the HUD closes, so the app can re-home onto it.
    setSession: sessionId => ipcRenderer.send('reign:hud:session', sessionId),
    onGoto: callback => {
      const listener = (_event, sessionId) => callback(sessionId)
      ipcRenderer.on('reign:hud:goto', listener)

      return () => ipcRenderer.removeListener('reign:hud:goto', listener)
    },
    onChanged: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('reign:hud:changed', listener)

      return () => ipcRenderer.removeListener('reign:hud:changed', listener)
    },
    // Linux only, and silent elsewhere: where the cursor is, in page
    // coordinates, or null when it has left the window. Stands in for the
    // mousemove that `setIgnoreMouseEvents(true, { forward: true })` delivers on
    // macOS and Windows but not here.
    onCursor: callback => {
      const listener = (_event, point) => callback(point)
      ipcRenderer.on('reign:hud:cursor', listener)

      return () => ipcRenderer.removeListener('reign:hud:cursor', listener)
    },
    // Main's game-overlay watch: whether a fullscreen app (a game) is under
    // the HUD, so the renderer can step back to the low-opacity overlay
    // treatment while one owns the screen.
    onGameOverlay: callback => {
      const listener = (_event, state) => callback(state)
      ipcRenderer.on('reign:hud:game-overlay', listener)

      return () => ipcRenderer.removeListener('reign:hud:game-overlay', listener)
    }
  },
  // Quick Entry: the global-hotkey mini composer window. Main owns the OS
  // shortcut + the persisted preference; the quick window only captures text
  // and hands it back, and the primary renderer submits it through the normal
  // prompt path.
  quickEntry: {
    getSettings: () => ipcRenderer.invoke('reign:quick-entry:settings:get'),
    setSettings: patch => ipcRenderer.invoke('reign:quick-entry:settings:set', patch),
    submit: payload => ipcRenderer.send('reign:quick-entry:submit', payload),
    dismiss: () => ipcRenderer.send('reign:quick-entry:dismiss'),
    // Primary renderer → main → quick window: gateway connection state + the
    // recent-session options the target picker offers. Main caches the latest
    // payload so a freshly spawned quick window starts from truth.
    pushState: payload => ipcRenderer.send('reign:quick-entry:state', payload),
    // Quick window subscribes to those pushes.
    onState: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:quick-entry:state', listener)

      return () => ipcRenderer.removeListener('reign:quick-entry:state', listener)
    },
    // Main → primary renderer: a submit captured by the quick window.
    onSubmit: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:quick-entry:submit', listener)

      return () => ipcRenderer.removeListener('reign:quick-entry:submit', listener)
    },
    // Main → quick window: you were just summoned (reset draft + refocus).
    onShown: callback => {
      const listener = () => callback()
      ipcRenderer.on('reign:quick-entry:shown', listener)

      return () => ipcRenderer.removeListener('reign:quick-entry:shown', listener)
    }
  },
  getBootProgress: () => ipcRenderer.invoke('reign:boot-progress:get'),
  getConnectionConfig: profile => ipcRenderer.invoke('reign:connection-config:get', profile),
  saveConnectionConfig: payload => ipcRenderer.invoke('reign:connection-config:save', payload),
  applyConnectionConfig: payload => ipcRenderer.invoke('reign:connection-config:apply', payload),
  testConnectionConfig: payload => ipcRenderer.invoke('reign:connection-config:test', payload),
  // Opt-in OS-keychain encryption for stored gateway secrets (default off —
  // see secret-storage-policy.ts). get never touches the OS keychain.
  getSecretStorageEncryption: () => ipcRenderer.invoke('reign:secret-storage:get'),
  setSecretStorageEncryption: (on: boolean) => ipcRenderer.invoke('reign:secret-storage:set', on),
  // v2 multi-connection registry: named agent sources (local / remote / cloud / ssh).
  connections: {
    list: () => ipcRenderer.invoke('reign:connections:list'),
    save: payload => ipcRenderer.invoke('reign:connections:save', payload),
    remove: id => ipcRenderer.invoke('reign:connections:remove', id),
    setPrimary: id => ipcRenderer.invoke('reign:connections:set-primary', id),
    setLaunchMode: mode => ipcRenderer.invoke('reign:connections:set-launch-mode', mode),
    setLastUsed: id => ipcRenderer.invoke('reign:connections:set-last-used', id),
    test: id => ipcRenderer.invoke('reign:connections:test', id),
    updateManaged: id => ipcRenderer.invoke('reign:connections:update-managed', id),
    // Fan out `reign update` to every eligible registered connection.
    // Optional excludeIds skips rows the caller updates through another path.
    updateAll: options => ipcRenderer.invoke('reign:connections:update-all', options),
    // Registry lifecycle push (main → renderer): a connection was removed or
    // materially edited, so secondaries scoped to it must be disposed (and,
    // for edits, re-dialed at the new target).
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:connections:changed', listener)

      return () => ipcRenderer.removeListener('reign:connections:changed', listener)
    }
  },
  sshConfigHosts: () => ipcRenderer.invoke('reign:ssh-config:hosts'),
  sshResolveHost: host => ipcRenderer.invoke('reign:ssh-config:resolve', host),
  probeConnectionConfig: remoteUrl => ipcRenderer.invoke('reign:connection-config:probe', remoteUrl),
  oauthLoginConnectionConfig: remoteUrl => ipcRenderer.invoke('reign:connection-config:oauth-login', remoteUrl),
  oauthLogoutConnectionConfig: remoteUrl => ipcRenderer.invoke('reign:connection-config:oauth-logout', remoteUrl),
  // Reign Cloud: one portal login powers discovery + silent per-agent sign-in
  // (cloud-auto-discovery Phase 3).
  cloud: {
    status: () => ipcRenderer.invoke('reign:cloud:status'),
    login: () => ipcRenderer.invoke('reign:cloud:login'),
    logout: () => ipcRenderer.invoke('reign:cloud:logout'),
    discover: org => ipcRenderer.invoke('reign:cloud:discover', org),
    agentSignIn: dashboardUrl => ipcRenderer.invoke('reign:cloud:agent-sign-in', dashboardUrl)
  },
  profile: {
    get: () => ipcRenderer.invoke('reign:profile:get'),
    remember: name => ipcRenderer.invoke('reign:profile:remember', name),
    set: name => ipcRenderer.invoke('reign:profile:set', name)
  },
  api: request => ipcRenderer.invoke('reign:api', request),
  notify: payload => ipcRenderer.invoke('reign:notify', payload),
  requestMicrophoneAccess: () => ipcRenderer.invoke('reign:requestMicrophoneAccess'),
  readWindowBelow: () => ipcRenderer.invoke('reign:window:readBelow'),
  readFileDataUrl: filePath => ipcRenderer.invoke('reign:readFileDataUrl', filePath),
  readFileDataUrlForAttach: filePath => ipcRenderer.invoke('reign:readFileDataUrlForAttach', filePath),
  dataUrlReadMax: {
    get: () => ipcRenderer.invoke('reign:data-url-read-max:get'),
    set: maxMb => ipcRenderer.invoke('reign:data-url-read-max:set', maxMb)
  },
  readFileText: filePath => ipcRenderer.invoke('reign:readFileText', filePath),
  readPluginSource: (filePath: string) => ipcRenderer.invoke('reign:readPluginSource', filePath),
  selectPaths: options => ipcRenderer.invoke('reign:selectPaths', options),
  selectSavePath: options => ipcRenderer.invoke('reign:selectSavePath', options),
  writeClipboard: text => ipcRenderer.invoke('reign:writeClipboard', text),
  readClipboard: () => ipcRenderer.invoke('reign:readClipboard'),
  saveGatewayFile: payload => ipcRenderer.invoke('reign:saveGatewayFile', payload),
  saveImageFromUrl: url => ipcRenderer.invoke('reign:saveImageFromUrl', url),
  contextMenuEdit: command => ipcRenderer.invoke('reign:context-menu:edit', command),
  contextMenuCopyImage: () => ipcRenderer.invoke('reign:context-menu:copy-image'),
  contextMenuSpellcheck: action => ipcRenderer.invoke('reign:context-menu:spellcheck', action),
  contextMenuGuestAddWord: payload => ipcRenderer.invoke('reign:context-menu:guest-add-word', payload),
  onContextMenuSpellcheck: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:context-menu-spellcheck', listener)

    return () => ipcRenderer.removeListener('reign:context-menu-spellcheck', listener)
  },
  saveImageBuffer: (data, ext, name) => ipcRenderer.invoke('reign:saveImageBuffer', { data, ext, name }),
  capturePreview: payload => ipcRenderer.invoke('reign:capturePreview', payload),
  saveClipboardImage: () => ipcRenderer.invoke('reign:saveClipboardImage'),
  getPathForFile: file => {
    try {
      return webUtils.getPathForFile(file) || ''
    } catch {
      return ''
    }
  },
  normalizePreviewTarget: (target, baseDir) => ipcRenderer.invoke('reign:normalizePreviewTarget', target, baseDir),
  watchPreviewFile: url => ipcRenderer.invoke('reign:watchPreviewFile', url),
  watchDirectory: dir => ipcRenderer.invoke('reign:watchDirectory', dir),
  stopPreviewFileWatch: id => ipcRenderer.invoke('reign:stopPreviewFileWatch', id),
  setActiveWork: payload => ipcRenderer.send('reign:active-work', payload),
  setTitleBarTheme: payload => ipcRenderer.send('reign:titlebar-theme', payload),
  setNativeTheme: mode => ipcRenderer.send('reign:native-theme', mode),
  setTranslucency: payload => ipcRenderer.send('reign:translucency', payload),
  setKeepAwake: on => ipcRenderer.send('reign:keep-awake', on),
  setDisableF12: blocked => ipcRenderer.send('reign:devtools:disable-f12', blocked),
  setPreviewShortcutActive: active => ipcRenderer.send('reign:previewShortcutActive', Boolean(active)),
  openExternal: url => ipcRenderer.invoke('reign:openExternal', url),
  mcpOauth: {
    // One-shot loopback listener for MCP OAuth against remote backends: bind
    // on this machine, hand redirectUri to mcp.servers.oauth.start, then wait
    // for the provider redirect and relay code/state via oauth.callback.
    listen: () => ipcRenderer.invoke('reign:mcp-oauth:listen'),
    wait: (id, timeoutMs) => ipcRenderer.invoke('reign:mcp-oauth:wait', id, timeoutMs),
    cancel: id => ipcRenderer.invoke('reign:mcp-oauth:cancel', id)
  },
  openPreviewInBrowser: url => ipcRenderer.invoke('reign:openPreviewInBrowser', url),
  reachPreviewUrl: url => ipcRenderer.invoke('reign:preview:reach', url),
  setActiveConnectionRoute: route => ipcRenderer.send('reign:connection:active-route', route),
  fetchLinkTitle: url => ipcRenderer.invoke('reign:fetchLinkTitle', url),
  resolveFavicon: url => ipcRenderer.invoke('reign:resolveFavicon', url),
  sanitizeWorkspaceCwd: cwd => ipcRenderer.invoke('reign:workspace:sanitize', cwd),
  settings: {
    getDefaultProjectDir: () => ipcRenderer.invoke('reign:setting:defaultProjectDir:get'),
    setDefaultProjectDir: dir => ipcRenderer.invoke('reign:setting:defaultProjectDir:set', dir),
    pickDefaultProjectDir: () => ipcRenderer.invoke('reign:setting:defaultProjectDir:pick')
  },
  zoom: {
    // Current zoom of this window, as { level, percent }.
    get: () => ipcRenderer.invoke('reign:zoom:get'),
    // Synchronous zoom factor (1 = 100%). Coordinate math needs it in the
    // same tick as the event it converts, so no IPC round-trip here.
    factor: () => webFrame.getZoomFactor(),
    setPercent: percent => ipcRenderer.send('reign:zoom:set-percent', percent),
    // Fires on every zoom change, including the Ctrl/Cmd +/-/0 shortcuts,
    // so the settings UI can stay in sync with the keyboard.
    onChanged: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:zoom:changed', listener)

      return () => ipcRenderer.removeListener('reign:zoom:changed', listener)
    }
  },
  revealLogs: () => ipcRenderer.invoke('reign:logs:reveal'),
  getRecentLogs: () => ipcRenderer.invoke('reign:logs:recent'),
  // Fire-and-forget: persists a renderer error-boundary catch (with component
  // stack) to desktop.log so crashes survive the window (#79428).
  reportRendererError: report => ipcRenderer.send('reign:logs:renderer-error', report),
  readDir: dirPath => ipcRenderer.invoke('reign:fs:readDir', dirPath),
  gitRoot: startPath => ipcRenderer.invoke('reign:fs:gitRoot', startPath),
  revealPath: targetPath => ipcRenderer.invoke('reign:fs:reveal', targetPath),
  openDir: dirPath => ipcRenderer.invoke('reign:fs:openDir', dirPath),
  desktopPluginsRoot: () => ipcRenderer.invoke('reign:fs:desktopPluginsRoot'),
  logsRoot: () => ipcRenderer.invoke('reign:fs:logsRoot'),
  agentPluginsRoot: () => ipcRenderer.invoke('reign:fs:agentPluginsRoot'),
  renamePath: (targetPath, newName) => ipcRenderer.invoke('reign:fs:rename', targetPath, newName),
  writeTextFile: (filePath, content) => ipcRenderer.invoke('reign:fs:writeText', filePath, content),
  trashPath: targetPath => ipcRenderer.invoke('reign:fs:trash', targetPath),
  git: {
    worktreeList: repoPath => ipcRenderer.invoke('reign:git:worktreeList', repoPath),
    worktreeAdd: (repoPath, options) => ipcRenderer.invoke('reign:git:worktreeAdd', repoPath, options),
    worktreeRemove: (repoPath, worktreePath, options) =>
      ipcRenderer.invoke('reign:git:worktreeRemove', repoPath, worktreePath, options),
    branchSwitch: (repoPath, branch) => ipcRenderer.invoke('reign:git:branchSwitch', repoPath, branch),
    branchList: repoPath => ipcRenderer.invoke('reign:git:branchList', repoPath),
    baseBranchList: repoPath => ipcRenderer.invoke('reign:git:baseBranchList', repoPath),
    repoStatus: repoPath => ipcRenderer.invoke('reign:git:repoStatus', repoPath),
    fileDiff: (repoPath, filePath) => ipcRenderer.invoke('reign:git:fileDiff', repoPath, filePath),
    scanRepos: (roots, options) => ipcRenderer.invoke('reign:git:scanRepos', roots, options),
    review: {
      list: (repoPath, scope, baseRef) => ipcRenderer.invoke('reign:git:review:list', repoPath, scope, baseRef),
      diff: (repoPath, filePath, scope, baseRef, staged) =>
        ipcRenderer.invoke('reign:git:review:diff', repoPath, filePath, scope, baseRef, staged),
      stage: (repoPath, filePath) => ipcRenderer.invoke('reign:git:review:stage', repoPath, filePath),
      unstage: (repoPath, filePath) => ipcRenderer.invoke('reign:git:review:unstage', repoPath, filePath),
      revert: (repoPath, filePath) => ipcRenderer.invoke('reign:git:review:revert', repoPath, filePath),
      revParse: (repoPath, ref) => ipcRenderer.invoke('reign:git:review:revParse', repoPath, ref),
      commit: (repoPath, message, push) => ipcRenderer.invoke('reign:git:review:commit', repoPath, message, push),
      commitContext: repoPath => ipcRenderer.invoke('reign:git:review:commitContext', repoPath),
      push: repoPath => ipcRenderer.invoke('reign:git:review:push', repoPath),
      shipInfo: repoPath => ipcRenderer.invoke('reign:git:review:shipInfo', repoPath),
      prList: (repoPath, branches, numbers) =>
        ipcRenderer.invoke('reign:git:review:prList', repoPath, branches, numbers),
      fetchPrComment: (repoPath, url) => ipcRenderer.invoke('reign:git:review:fetchPrComment', repoPath, url),
      createPr: repoPath => ipcRenderer.invoke('reign:git:review:createPr', repoPath)
    }
  },
  terminal: {
    attach: id => ipcRenderer.invoke('reign:terminal:attach', id),
    cwd: id => ipcRenderer.invoke('reign:terminal:cwd', id),
    dispose: id => ipcRenderer.invoke('reign:terminal:dispose', id),
    resize: (id, size) => ipcRenderer.invoke('reign:terminal:resize', id, size),
    start: options => ipcRenderer.invoke('reign:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('reign:terminal:write', id, data),
    onData: (id, callback) => {
      const channel = `reign:terminal:${id}:data`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    },
    onExit: (id, callback) => {
      const channel = `reign:terminal:${id}:exit`
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on(channel, listener)

      return () => ipcRenderer.removeListener(channel, listener)
    }
  },
  onClosePreviewRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:close-preview-requested', listener)

    return () => ipcRenderer.removeListener('reign:close-preview-requested', listener)
  },
  onPreviewNav: callback => {
    const listener = (_event, command) => callback(command)
    ipcRenderer.on('reign:preview-nav', listener)

    return () => ipcRenderer.removeListener('reign:preview-nav', listener)
  },
  onOpenFolderRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:open-folder-requested', listener)

    return () => ipcRenderer.removeListener('reign:open-folder-requested', listener)
  },
  onOpenUpdatesRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:open-updates', listener)

    return () => ipcRenderer.removeListener('reign:open-updates', listener)
  },
  onDeepLink: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:deep-link', listener)

    return () => ipcRenderer.removeListener('reign:deep-link', listener)
  },
  signalDeepLinkReady: () => ipcRenderer.invoke('reign:deep-link-ready'),
  probePluginRepo: payload => ipcRenderer.invoke('reign:plugin:probe', payload),
  installDesktopPlugin: payload => ipcRenderer.invoke('reign:plugin:installDesktop', payload),
  onWindowStateChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:window-state-changed', listener)

    return () => ipcRenderer.removeListener('reign:window-state-changed', listener)
  },
  onFocusSession: callback => {
    const listener = (_event, sessionId) => callback(sessionId)
    ipcRenderer.on('reign:focus-session', listener)

    return () => ipcRenderer.removeListener('reign:focus-session', listener)
  },
  onNotificationAction: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:notification-action', listener)

    return () => ipcRenderer.removeListener('reign:notification-action', listener)
  },
  onNotificationActivate: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:notification-activate', listener)

    return () => ipcRenderer.removeListener('reign:notification-activate', listener)
  },
  onPreviewFileChanged: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:preview-file-changed', listener)

    return () => ipcRenderer.removeListener('reign:preview-file-changed', listener)
  },
  onBackendExit: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:backend-exit', listener)

    return () => ipcRenderer.removeListener('reign:backend-exit', listener)
  },
  // Soft gateway-mode apply finished tearing down the primary backend. Renderer
  // should wipe session lists + re-dial without a window reload.
  onConnectionApplied: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:connection:applied', listener)

    return () => ipcRenderer.removeListener('reign:connection:applied', listener)
  },
  onPowerResume: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:power-resume', listener)

    return () => ipcRenderer.removeListener('reign:power-resume', listener)
  },
  // AC ↔ battery transitions; renderers slow their backstop polls on battery.
  getOnBattery: () => ipcRenderer.invoke('reign:power-battery:get'),
  onBatteryChanged: callback => {
    const listener = (_event, onBattery) => callback(Boolean(onBattery))
    ipcRenderer.on('reign:power-battery', listener)

    return () => ipcRenderer.removeListener('reign:power-battery', listener)
  },
  onBootProgress: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:boot-progress', listener)

    return () => ipcRenderer.removeListener('reign:boot-progress', listener)
  },
  // First-launch bootstrap progress -- emitted by the install.ps1 stage
  // runner in main.ts (apps/desktop/electron/bootstrap-runner.ts).
  // Renderer's install overlay subscribes to live events and queries the
  // current snapshot via getBootstrapState() to recover after a devtools
  // reload mid-bootstrap.
  getBootstrapState: () => ipcRenderer.invoke('reign:bootstrap:get'),
  continueBootstrapLocal: () => ipcRenderer.invoke('reign:bootstrap:continue-local'),
  recycleBackend: profile => ipcRenderer.invoke('reign:backend:recycle', profile),
  resetBootstrap: () => ipcRenderer.invoke('reign:bootstrap:reset'),
  repairBootstrap: () => ipcRenderer.invoke('reign:bootstrap:repair'),
  cancelBootstrap: () => ipcRenderer.invoke('reign:bootstrap:cancel'),
  onBootstrapEvent: callback => {
    const listener = (_event, payload) => callback(payload)
    ipcRenderer.on('reign:bootstrap:event', listener)

    return () => ipcRenderer.removeListener('reign:bootstrap:event', listener)
  },
  getVersion: () => ipcRenderer.invoke('reign:version'),
  getRemoteDisplayReason: () => ipcRenderer.invoke('reign:get-remote-display-reason'),
  uninstall: {
    summary: () => ipcRenderer.invoke('reign:uninstall:summary'),
    run: mode => ipcRenderer.invoke('reign:uninstall:run', { mode })
  },
  updates: {
    check: () => ipcRenderer.invoke('reign:updates:check'),
    apply: opts => ipcRenderer.invoke('reign:updates:apply', opts),
    getBranch: () => ipcRenderer.invoke('reign:updates:branch:get'),
    setBranch: name => ipcRenderer.invoke('reign:updates:branch:set', name),
    onProgress: callback => {
      const listener = (_event, payload) => callback(payload)
      ipcRenderer.on('reign:updates:progress', listener)

      return () => ipcRenderer.removeListener('reign:updates:progress', listener)
    }
  },
  themes: {
    fetchMarketplace: id => ipcRenderer.invoke('reign:vscode-theme:fetch', id),
    searchMarketplace: query => ipcRenderer.invoke('reign:vscode-theme:search', query)
  },
  // Find-in-page (Ctrl/Cmd+F): delegates to Electron's
  // webContents.findInPage on the IPC sender's window so a Cmd+F pressed
  // in a secondary session window searches THAT window, not the primary.
  // `onFoundInPage` returns the unsubscribe fn; the renderer wires it via
  // `initFindInPageListener` in store/find-in-page.ts and tears it down
  // when the FindBar unmounts.
  findInPage: (query, options) => ipcRenderer.invoke('reign:find-in-page', query, options),
  stopFindInPage: () => ipcRenderer.invoke('reign:stop-find-in-page'),
  onFoundInPage: callback => {
    const listener = (_event, result) => callback(result)
    ipcRenderer.on('reign:found-in-page', listener)

    return () => ipcRenderer.removeListener('reign:found-in-page', listener)
  },
  // Main-process `before-input-event` forwards Ctrl/Cmd+F here so renderer
  // can open the FindBar even when the GTK compositor has already grabbed
  // the chord at the windowing layer (#81727).
  onOpenFindBarRequested: callback => {
    const listener = () => callback()
    ipcRenderer.on('reign:open-find-bar', listener)

    return () => ipcRenderer.removeListener('reign:open-find-bar', listener)
  }
})
