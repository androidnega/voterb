/**
 * Turn a DRF/axios error into a user-facing message.
 * Prefer friendlyFeedback helpers for student-facing flows.
 */
import { friendlyActionError, friendlyLoadError } from '@/utils/friendlyFeedback'

export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  return friendlyActionError(error, fallback)
}

export function parseLoadError(error, subject = 'this page') {
  return friendlyLoadError(error, subject)
}
