import type { Translations } from '@/i18n'
import { Archive, CloudUpload, type IconComponent } from '@/lib/icons'
import { servedByReignCloud } from '@/lib/reign-cloud-host'

export const BACKUP_SETTINGS_HREF = '/settings?tab=backup'

/** The query param naming the cloud agent to preselect in the transfer list. */
export const CLOUD_AGENT_PARAM = 'cloudAgent'

/** The old `/move-to-cloud?agent=<name>` route (the portal's `reign://open/move-to-cloud` link)
 *  → Settings ▸ Backup & Transfer, keeping the agent it names. */
export function backupSettingsHrefForLegacy(search: string): string {
  const agent = (new URLSearchParams(search).get('agent') ?? '').trim()

  return agent ? `${BACKUP_SETTINGS_HREF}&${new URLSearchParams({ [CLOUD_AGENT_PARAM]: agent })}` : BACKUP_SETTINGS_HREF
}

export interface BackupPaletteEntry {
  icon: IconComponent
  id: string
  keywords: string[]
  label: string
}

/** The ⌘K rows that open Settings ▸ Backup & Transfer: one per task. A Webapp Reign Cloud serves
 *  is a cloud agent itself, so it gets the backup row only. */
export function backupPaletteEntries(t: Translations): BackupPaletteEntry[] {
  const copy = t.settings.backup

  return [
    {
      icon: Archive,
      id: 'backup-agent',
      keywords: ['backup', 'export', 'archive', 'save', 'download', 'settings'],
      label: copy.backupCommand
    },
    ...(servedByReignCloud()
      ? []
      : [
          {
            icon: CloudUpload,
            id: 'transfer-to-cloud',
            keywords: ['move', 'migrate', 'cloud', 'reign cloud', 'upload', 'transfer', 'replace', 'settings'],
            label: copy.transferCommand
          }
        ])
  ]
}
