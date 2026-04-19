/**
 * @param {Record<string, unknown>} status
 * @returns {string[]}
 */
export function parseSourceFilesFromStatus(status) {
  const raw = status?.source_files
  if (Array.isArray(raw) && raw.length) {
    return raw.map(String).filter(Boolean)
  }
  const combined = status?.source_file
  if (typeof combined !== 'string' || !combined.trim()) {
    return []
  }
  return combined
    .split(/\s*\+\s*/)
    .map((s) => s.trim())
    .filter(Boolean)
}

/**
 * Map indexed filenames to UG / PG (NUST demo uses UG_Handbook.pdf / PG_Handbook.pdf).
 * @param {string[]} files
 * @returns {{ ug: string | undefined, pg: string | undefined }}
 */
export function resolveHandbookFiles(files) {
  const list = Array.isArray(files) ? files : []
  const ug =
    list.find((f) => f === 'UG_Handbook.pdf') ??
    list.find((f) => /ug/i.test(f) && !/pg/i.test(f))
  const pg =
    list.find((f) => f === 'PG_Handbook.pdf') ?? list.find((f) => /pg/i.test(f))
  return { ug, pg }
}
