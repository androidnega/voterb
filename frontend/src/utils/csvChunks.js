/**
 * Split a CSV File into smaller Blob chunks (same header on each)
 * so large imports can be queued without request timeouts.
 */

const DEFAULT_ROWS_PER_CHUNK = 250

export async function splitCsvFile(file, rowsPerChunk = DEFAULT_ROWS_PER_CHUNK) {
  const text = await file.text()
  const lines = text.replace(/^\uFEFF/, '').split(/\r\n|\n|\r/)
  const nonEmpty = lines.filter((line, idx) => idx === 0 || line.trim().length > 0)
  if (nonEmpty.length < 2) {
    throw new Error('CSV must include a header row and at least one voter row.')
  }

  const header = nonEmpty[0]
  const dataRows = nonEmpty.slice(1)
  const chunks = []

  for (let i = 0; i < dataRows.length; i += rowsPerChunk) {
    const slice = dataRows.slice(i, i + rowsPerChunk)
    const body = [header, ...slice].join('\n')
    const blob = new Blob([body], { type: 'text/csv' })
    const name = file.name?.replace(/\.csv$/i, '') || 'register'
    chunks.push({
      blob,
      fileName: `${name}-part${chunks.length + 1}.csv`,
      rowCount: slice.length,
    })
  }

  return {
    header,
    totalRows: dataRows.length,
    chunks,
  }
}
