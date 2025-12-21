export function exportToCSV<T extends Record<string, any>>(
  data: T[],
  filename: string,
  headers?: Record<keyof T, string>
) {
  if (!data || data.length === 0) {
    throw new Error('No data to export')
  }

  // Get headers from first object or use provided headers
  const keys = Object.keys(data[0]) as Array<keyof T>
  const headerLabels = headers || ({} as Record<keyof T, string>)

  // Create CSV header row
  const csvHeaders = keys.map((key) => headerLabels[key] || String(key))
  const csvRows = [csvHeaders.join(',')]

  // Create CSV data rows
  data.forEach((row) => {
    const values = keys.map((key) => {
      const value = row[key]
      if (value === null || value === undefined) return ''
      // Escape commas and quotes in values
      const stringValue = String(value).replace(/"/g, '""')
      return `"${stringValue}"`
    })
    csvRows.push(values.join(','))
  })

  // Create CSV content
  const csvContent = csvRows.join('\n')

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export function formatDateForCSV(date: string | Date): string {
  return new Date(date).toLocaleString()
}

