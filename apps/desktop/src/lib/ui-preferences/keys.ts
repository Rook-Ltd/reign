/**
 * Which persisted keys are machine-level UI preferences (#145213).
 *
 * Only these leave localStorage for the machine's shared store, so native
 * Desktop and every browser that opens this machine's Webapp show the same
 * choices. Scoped families keep their scope inside the key name (a
 * `….profile.<name>` or per-connection suffix): only the location changes.
 *
 * Deliberately NOT here (they stay in this browser/window):
 * - credentials, grants and connection config: gateway registry, custom model
 *   endpoints, plugin decisions and preview-script grants, embed permissions;
 * - per-window or per-device runtime state: layout tree, open tiles and tabs,
 *   last route/session, scroll, zoom, pet and popout geometry, keep-awake;
 * - drafts, queues, journals and caches: composer queue, in-flight turns,
 *   pending/prepared submissions, previews, pricing, backend skin cache, the
 *   "provider configured" onboarding cache (each backend answers that itself);
 * - one-off notices: butterbar, update and real-profile prompts.
 */

const SHARED_KEYS: ReadonlySet<string> = new Set([
  // Appearance.
  'reign-desktop-theme-v2',
  'reign-desktop-mode-v1',
  'reign-desktop-profile-themes-v1',
  'reign-desktop-profile-modes-v1',
  'reign-desktop-user-themes-v1',
  'reign.desktop.backdrop.v1',
  'reign.desktop.chat-text-scale.v1',
  'reign.desktop.interfaceMode.v1',
  'reign.desktop.textDirection',
  'reign.desktop.translucency.v2',
  'reign.desktop.user-bubble-transparency.v1',
  // Sessions sidebar and profile rail.
  'reign.desktop.agentsGroupedByWorkspace',
  'reign.desktop.profileColors',
  'reign.desktop.profileOrder',
  'reign.desktop.profileRailVisible',
  'reign.desktop.sessionListDensity',
  'reign.desktop.sessionOrder',
  'reign.desktop.sessionOrder.manual',
  'reign.desktop.showAllProfiles',
  'reign.desktop.sidebarAgentsGrouped.allProfiles',
  'reign.desktop.sidebarCardRows',
  'reign.desktop.sidebarGrouping',
  'reign.desktop.sidebarGrouping.allProfiles',
  'reign.desktop.sidebarRowMeta',
  'reign.desktop.sidebarShowAllSessions',
  'reign.desktop.sidebarShowArchived',
  'reign.desktop.sidebarSortKey',
  // Status bar.
  'reign.desktop.statusbarHidden.v2',
  'reign.desktop.statusbarVisible.v2',
  // Transcript and tools.
  'reign.desktop.hideThreadTimeline',
  'reign.desktop.reasoning.collapsedByDefault',
  'reign.desktop.toolView.hideCodeDiffs',
  'reign.desktop.toolView.technical',
  // Shell, panes and behaviour.
  'reign.desktop.alwaysExternalLinks.v1',
  'reign.desktop.capabilities.catalogCardView',
  'reign.desktop.composerPopout.enabled',
  'reign.desktop.composerPopout.gesturesEnabled',
  'reign.desktop.files.showIgnored',
  'reign.desktop.keybinds',
  'reign.desktop.layoutPresets.v2',
  'reign.desktop.panesFlipped',
  'reign.desktop.tabStripDefault',
  'reign.desktop.titlebarAppActions',
  // Guidance: what the user already skipped, saw or dismissed does not come
  // back in every new browser or origin (#145600).
  'reign-onboarding-skipped-v1',
  'reign.desktop.tips.last.v1',
  'reign.desktop.tips.next.v1',
  'reign.desktop.tips.retired.v1',
  'reign.desktop.tips.rotation.v1',
  'reign.desktop.tips.shownAt.v1',
  'reign.desktop.tours.v1',
  // Sound and media.
  'reign.desktop.autoSpeakReplies',
  'reign.desktop.completionSoundVariantId',
  'reign.desktop.hapticsMuted',
  'reign.desktop.videoPlaybackSpeed',
  // Model picker.
  'reign.desktop.collapsed-providers',
  'reign.desktop.favorite-models',
  // visible-models is a diff against known-models: they only make sense together.
  'reign.desktop.known-models',
  'reign.desktop.model-presets',
  'reign.desktop.visible-models'
])

/** Families whose scope rides in the key suffix (gateway aliases/order/collapsed). */
const SHARED_PREFIXES: readonly string[] = ['reign.desktop.sidebar.gatewayGroups.v1.']

export function isSharedPreferenceKey(key: string): boolean {
  return SHARED_KEYS.has(key) || SHARED_PREFIXES.some(prefix => key.startsWith(prefix))
}
