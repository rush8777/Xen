// app/chat/page.tsx
import Layout from "@/components/xen/main/layout"
import ChatContainer from "@/components/xen/chat/chat-container"

export default function ChatPage() {
  return (
    <Layout>
      <div className="h-[calc(100vh-6rem)]">
        <ChatContainer />
      </div>
    </Layout>
  )
}
