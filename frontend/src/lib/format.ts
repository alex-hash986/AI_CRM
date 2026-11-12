export function money(amount: number | string, currency?: string | null): string {
  return new Intl.NumberFormat('ru-RU', {
    ...(currency ? { style: 'currency', currency } : {}),
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(Number(amount))
}

export function percent(value: number): string {
  return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 1 }).format(value)}%`
}

export function dateTime(value: string): string {
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function initials(value: string): string {
  return value.trim().split(/\s+/).slice(0, 2).map(word => word[0]?.toUpperCase()).join('')
}
