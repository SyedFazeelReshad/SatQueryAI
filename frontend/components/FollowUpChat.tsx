'use client';

import React, { useState } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { QueryResponse } from '@/types/analysis';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  model?: string;
  timestamp: string;
}

interface FollowUpChatProps {
  sessionId: string;
  initialContext?: string;
}

export const FollowUpChat: React.FC<FollowUpChatProps> = ({ sessionId, initialContext }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      text: initialContext || 'Hello! I am ready for follow-up questions about this satellite scene. Ask me anything about the detected features, spectral properties, or changes.',
      model: 'SatQuery Assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sampleQuestions = [
    'What is the vegetation coverage?',
    'What caused the biggest change?',
    'Are there any water bodies visible?',
    'Explain the confidence rating',
  ];

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputValue;
    if (!textToSend.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryText) setInputValue('');
    setIsLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
      const res = await fetch(`${apiUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          query: textToSend,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to query (${res.status})`);
      }

      const data: QueryResponse = await res.json();
      const assistantMessage: Message = {
        role: 'assistant',
        text: data.answer,
        model: data.model,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || 'Error contacting SatQuery backend');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Conversational Exploration</h3>
            <p className="text-[11px] text-slate-500">Contextual Q&A on session evidence</p>
          </div>
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 min-h-[220px] max-h-[380px] bg-white">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-2.5 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shrink-0 mt-0.5">
                <Bot className="w-3.5 h-3.5" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-lg px-3.5 py-2.5 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-emerald-600 text-white shadow-sm whitespace-pre-wrap'
                  : 'bg-slate-100 text-slate-800 border border-slate-200 shadow-sm'
              }`}
            >
              {msg.role === 'user' ? (
                <p>{msg.text}</p>
              ) : (
                <div className="prose prose-slate prose-xs max-w-none text-slate-800 leading-relaxed
                  prose-p:mb-1.5 prose-p:last:mb-0
                  prose-headings:text-slate-900 prose-headings:font-bold prose-headings:my-1 prose-headings:text-xs
                  prose-strong:text-slate-900 prose-strong:font-semibold
                  prose-ul:my-1 prose-ul:ml-3 prose-li:my-0.5
                  prose-table:text-[11px] prose-th:py-1 prose-td:py-1">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.text}
                  </ReactMarkdown>
                </div>
              )}
              <div
                className={`flex items-center justify-between mt-2 pt-1 border-t border-slate-200/50 text-[10px] ${
                  msg.role === 'user' ? 'text-emerald-100' : 'text-slate-500'
                }`}
              >
                <span>{msg.model || ''}</span>
                <span>{msg.timestamp}</span>
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 shrink-0 mt-0.5">
                <User className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <div className="w-7 h-7 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 animate-pulse">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-slate-100 rounded-lg px-3 py-2 border border-slate-200 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce delay-100" />
              <span className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-bounce delay-200" />
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center space-x-2 text-xs text-red-700 bg-red-50 border border-red-200 p-2.5 rounded-lg">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Suggested prompts pills */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 flex flex-wrap gap-1.5">
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            disabled={isLoading}
            className="text-[11px] px-2.5 py-1 rounded-full bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 transition-colors disabled:opacity-50 shadow-sm"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input bar */}
      <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center space-x-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a follow-up question..."
          disabled={isLoading}
          className="flex-1 bg-white border border-slate-300 rounded-lg px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all disabled:opacity-50"
        />
        <button
          onClick={() => handleSend()}
          disabled={!inputValue.trim() || isLoading}
          className="p-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

