import { HomeChatView } from '@/components/workspace/home-chat-view'
import { HomeEmptyState } from '@/components/workspace/home-empty-state'
import { useHomeChat } from '@/hooks/useHomeChat'

export function HomeView() {
  const { messages, isStarted, onSend, chatTitle, inputDisabled } =
    useHomeChat()

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
