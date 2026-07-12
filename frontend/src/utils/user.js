import { formatIndexDisplay } from '@/utils/index'

export function displayUserName(user, fallback = 'User') {
  if (!user) return fallback

  if (user.display_name) return user.display_name

  const parts = [user.first_name, user.last_name].filter(Boolean)
  if (parts.length) return parts.join(' ')

  if (user.email) return user.email.split('@')[0]
  if (user.index_number) return formatIndexDisplay(user.index_number)

  return fallback
}
