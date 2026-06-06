import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { Message } from '../types';

interface Props {
  messages: Message[];
  loading?: boolean;
  thinkingStatus?: string;
}

export const ChatPanel: React.FC<Props> = ({ messages, loading, thinkingStatus }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg p-4 shadow-md ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800'
            }`}
          >
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const inline = !match;
                    return !inline ? (
                      <SyntaxHighlighter
                        language={match[1]}
                        PreTag="div"
                        className="rounded-md text-sm"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>

            {message.sources && message.sources.length > 0 && (
              <div className={`mt-3 pt-3 border-t text-sm ${
                message.role === 'user' ? 'border-blue-500' : 'border-gray-200'
              }`}>
                <div className={`font-semibold mb-2 ${
                  message.role === 'user' ? 'text-blue-200' : 'text-gray-600'
                }`}>
                  📖 引用来源：
                </div>
                {message.sources.map((source: any, idx: number) => (
                  <div
                    key={idx}
                    className={`p-2 rounded mb-1 text-xs ${
                      message.role === 'user' ? 'bg-blue-700' : 'bg-gray-50'
                    }`}
                  >
                    <div className="truncate">{source.content}</div>
                    {source.metadata?.source && (
                      <div className={`mt-1 ${
                        message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                      }`}>
                        来源：{source.metadata.source}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {message.toolsUsed && message.toolsUsed.length > 0 && (
              <div className={`mt-2 text-xs ${
                message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
              }`}>
                🔧 使用工具：{message.toolsUsed.join(', ')}
              </div>
            )}

            <div className={`text-xs mt-2 ${
              message.role === 'user' ? 'text-blue-200' : 'text-gray-400'
            }`}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
      {/* 思考中指示器 */}
      {thinkingStatus && (
        <div className="flex justify-start">
          <div className="bg-gray-50 rounded-lg p-3 shadow-md border border-gray-200 animate-pulse">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}></span>
              </span>
              <span>思考中：{thinkingStatus}</span>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
