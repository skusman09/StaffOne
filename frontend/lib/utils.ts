export const getFullAvatarUrl = (url?: string | null) => {
    if (!url) return null
    if (url.startsWith('http')) return url
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
    return `${baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl}${url}`
}
