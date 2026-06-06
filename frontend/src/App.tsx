import React, { useState } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { ChatInput } from './components/ChatInput';
import { DocumentUpload } from './components/DocumentUpload';
import { Message } from './types';
import { sendChatStream, uploadDocument, getDocumentCount, clearDocuments, listSessions, getSession } from './utils/api';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [documentCount, setDocumentCount] = useState(0);
  const [sessionId, setSessionId] = useState<string>('');

  // 初始化：加载最近会话
  React.useEffect(() => {
    fetchDocumentCount();
    loadLatestSession();
  }, []);

  const loadLatestSession = async () => {
    try {
      const sessions = await listSessions();
      if (sessions.length > 0) {
        const latest = sessions[0];
        const data = await getSession(latest.id);
        setSessionId(latest.id);
        if (data.messages) {
          setMessages(
            data.messages.map((msg: any) => ({
              id: `${msg.timestamp}-${msg.role}`,
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.timestamp),
            }))
          );
        }
      }
    } catch (e) {
      console.error('加载会话失败:', e);
    }
  };

  const fetchDocumentCount = async () => {
    try {
      const count = await getDocumentCount();
      setDocumentCount(count);
    } catch (error) {
      console.error('获取文档数量失败:', error);
    }
  };

  const handleSend = async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    const assistantId = (Date.now() + 1).toString();

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setThinkingStatus('');

    try {
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
      }));

      let fullAnswer = '';

      await sendChatStream(question, history, (event) => {
        switch (event.type) {
          case 'thinking':
            setThinkingStatus(event.content);
            break;

          case 'session_id':
            if (!sessionId) {
              setSessionId(event.content);
            }
            break;

          case 'token':
            fullAnswer += event.content;
            setMessages((prev) => {
              const updated = [...prev];
              const existingIdx = updated.findIndex((m) => m.id === assistantId);
              const msg: Message = {
                id: assistantId,
                role: 'assistant',
                content: fullAnswer,
                timestamp: new Date(),
                sources: [],
                toolsUsed: [],
              };
              if (existingIdx >= 0) {
                updated[existingIdx] = msg;
              } else {
                updated.push(msg);
              }
              return updated;
            });
            break;

          case 'done':
            const sources = event.sources || [];
            const toolsUsed = event.tools_used || [];
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m.id === assistantId);
              if (idx >= 0) {
                updated[idx] = {
                  ...updated[idx],
                  sources,
                  toolsUsed,
                  content: fullAnswer || updated[idx].content,
                };
              }
              return updated;
            });
            break;

          case 'error':
            console.error('流式错误:', event.content);
            setMessages((prev) => {
              const updated = [...prev];
              const idx = updated.findIndex((m) => m.id === assistantId);
              if (idx >= 0) {
                updated[idx] = {
                  ...updated[idx],
                  content: `抱歉，发生了错误：${event.content}`,
                };
              } else {
                updated.push({
                  id: assistantId,
                  role: 'assistant',
                  content: `抱歉，发生了错误：${event.content}`,
                  timestamp: new Date(),
                });
              }
              return updated;
            });
            break;
        }
      }, sessionId);
    } catch (error) {
      console.error('发送消息失败:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: 'assistant',
          content: '抱歉，发生了错误。请稍后再试。',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
      setThinkingStatus('');
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const response = await uploadDocument(file);
      console.log('上传成功:', response);
      await fetchDocumentCount();
      alert(`文档上传成功！共 ${response.chunks_count} 个文档块`);
    } catch (error) {
      console.error('上传失败:', error);
      alert('文档上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = async () => {
    if (confirm('确定要清空知识库吗？')) {
      try {
        await clearDocuments();
        await fetchDocumentCount();
        alert('知识库已清空');
      } catch (error) {
        console.error('清空失败:', error);
        alert('清空失败，请重试');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <h1 className="text-2xl font-bold text-center">🤖 Agentic RAG 智能问答系统</h1>
      </header>

      <div className="container mx-auto p-4 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-1">
            <DocumentUpload
              onUpload={handleUpload}
              uploading={uploading}
              documentCount={documentCount}
              onClear={handleClear}
            />

            <div className="bg-white rounded-lg shadow-md p-4 mt-4">
              <h3 className="text-lg font-semibold mb-3 text-gray-800">💡 使用说明</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>1️⃣ 先上传文档到知识库</li>
                <li>2️⃣ 然后提问相关问题</li>
                <li>3️⃣ 支持数学计算，如"123+456等于多少"</li>
                <li>4️⃣ 支持名言，如"来一句格言"</li>
                <li>5️⃣ 支持IP查询，如"查一下8.8.8.8"</li>
              </ul>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md flex flex-col h-[600px]">
              <ChatPanel
                messages={messages}
                loading={loading}
                thinkingStatus={thinkingStatus}
              />
              <ChatInput onSend={handleSend} disabled={loading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;