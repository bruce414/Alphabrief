/**
 * Placeholder briefs for the Ask workspace. Replace with API data later.
 */
export type RecentBrief = {
  id: string
  title: string
  tags: readonly string[]
  sourceCount: number
  /** Pre-formatted short date for display */
  createdLabel: string
}

export const MOCK_RECENT_BRIEFS: RecentBrief[] = [
  {
    id: 'mock-1',
    title: "Nvidia's data-center moat after Blackwell",
    tags: ['semis', 'ai-infra', 'nvda'],
    sourceCount: 18,
    createdLabel: 'May 02',
  },
]
