import type { AnalysisMode } from '@/components/quick-chat/types'
import type { AnalyzeSourceParams } from '@/lib/quickChatApi'

const URL_IN_TEXT_PATTERN = /https?:\/\/\S+/i
const SINGLE_URL_PATTERN = /^https?:\/\/\S+$/i

const SOURCE_TEXT_MIN_CHARS = 200

export function inputContainsUrl(text: string): boolean {
  return URL_IN_TEXT_PATTERN.test(text)
}

export function isSingleUrl(text: string): boolean {
  return SINGLE_URL_PATTERN.test(text.trim())
}

export function detectAnalysisMode(text: string): AnalysisMode {
  const trimmed = text.trim()
  if (isSingleUrl(trimmed)) return 'source_analysis_with_map'
  if (trimmed.length > SOURCE_TEXT_MIN_CHARS) return 'source_analysis_with_map'
  return 'chat_only'
}

/** Map user input to analyze API fields (Prompt 5 §3). */
export function buildAnalyzePayload(text: string): AnalyzeSourceParams {
  const trimmed = text.trim()
  if (isSingleUrl(trimmed)) {
    return { sourceUrl: trimmed }
  }
  if (trimmed.length > SOURCE_TEXT_MIN_CHARS) {
    return { sourceText: trimmed }
  }
  return { userQuery: trimmed }
}
