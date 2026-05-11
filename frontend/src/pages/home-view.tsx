import { useOutletContext } from 'react-router-dom'

import { HomeChatView } from '@/components/workspace/home-chat-view'
import { HomeEmptyState } from '@/components/workspace/home-empty-state'
import { useHomeChat } from '@/hooks/useHomeChat'
import type { AppShellOutletContext } from '@/pages/app-shell'

export function HomeView() {
  const { activeChatId, setActiveChatId } =
    useOutletContext<AppShellOutletContext>()
  const { messages, isStarted, onSend, chatTitle, inputDisabled } =
    useHomeChat({
      selectedChatId: activeChatId,
      onChatCreated: setActiveChatId,
    })

  return isStarted ? (
    <HomeChatView
      chatTitle={chatTitle}
      messages={messages}
      onSend={onSend}
      inputDisabled={inputDisabled}
    />
  ) : (
    <HomeEmptyState onSend={onSend} inputDisabled={inputDisabled} />
  )
}
