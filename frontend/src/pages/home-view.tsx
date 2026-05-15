import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import useSWR from 'swr'

import {
  HomeChatView,
  type HomeChatTab,
} from '@/components/workspace/home-chat-view'
import { HomeEmptyState } from '@/components/workspace/home-empty-state'
import { useHomeChat } from '@/hooks/useHomeChat'
import { listChatSources } from '@/lib/workspaceApi'
import type { AppShellOutletContext } from '@/pages/app-shell'

export function HomeView() {
  const { activeChatId, setActiveChatId } =
    useOutletContext<AppShellOutletContext>()
  const {
    messages,
    isStarted,
    onSend,
    onFollowUpQuestion,
    chatTitle,
    inputDisabled,
    awaitingReply,
    stopGeneration,
    regenerateAssistant,
    chatId,
  } = useHomeChat({
    selectedChatId: activeChatId,
    onChatCreated: setActiveChatId,
  })

  const [activeTab, setActiveTab] = useState<HomeChatTab>('chat')

  // Reset to chat view when switching between chats.
  useEffect(() => {
    setActiveTab('chat')
  }, [chatId])

  const lastAssistantPending = messages.some(
    (m) => m.role === 'ai' && m.loading,
  )

  const {
    data: sourcesData,
    isLoading: sourcesLoading,
  } = useSWR(
    chatId ? (['chat-sources', chatId] as const) : null,
    () => listChatSources(chatId as string),
    {
      // Refresh while the assistant is working so newly fetched sources show up live.
      refreshInterval: lastAssistantPending ? 2000 : 0,
    },
  )

  return isStarted ? (
    <HomeChatView
      chatTitle={chatTitle}
      messages={messages}
      onSend={onSend}
      onFollowUpQuestion={onFollowUpQuestion}
      inputDisabled={inputDisabled}
      awaitingReply={awaitingReply}
      onStopGeneration={stopGeneration}
      onRegenerateAssistant={regenerateAssistant}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      sources={sourcesData?.items ?? []}
      sourcesLoading={Boolean(chatId && sourcesLoading)}
    />
  ) : (
    <HomeEmptyState
      onSend={onSend}
      inputDisabled={inputDisabled}
      awaitingReply={awaitingReply}
      onStopGeneration={stopGeneration}
    />
  )
}
