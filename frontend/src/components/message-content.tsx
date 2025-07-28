'use client'

import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface MessageContentProps {
  content: string
}

export function MessageContent({ content }: MessageContentProps) {
  return (
    <ReactMarkdown
      components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '')
          return !inline && match ? (
            <SyntaxHighlighter
              style={oneDark}
              language={match[1]}
              PreTag="div"
              className="rounded-md"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>
              {children}
            </code>
          )
        },
        p({ children }) {
          return <p className="mb-2 last:mb-0">{children}</p>
        },
        ul({ children }) {
          return <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
        },
        ol({ children }) {
          return <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
        },
        li({ children }) {
          return <li className="text-sm">{children}</li>
        },
        h1({ children }) {
          return <h1 className="text-xl font-bold mb-2">{children}</h1>
        },
        h2({ children }) {
          return <h2 className="text-lg font-semibold mb-2">{children}</h2>
        },
        h3({ children }) {
          return <h3 className="text-base font-semibold mb-2">{children}</h3>
        },
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-muted-foreground/20 pl-4 italic text-muted-foreground">
              {children}
            </blockquote>
          )
        },
        table({ children }) {
          return (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse border border-border">
                {children}
              </table>
            </div>
          )
        },
        th({ children }) {
          return (
            <th className="border border-border px-3 py-2 text-left font-semibold bg-muted">
              {children}
            </th>
          )
        },
        td({ children }) {
          return (
            <td className="border border-border px-3 py-2">
              {children}
            </td>
          )
        },
      }}
      className="prose prose-sm max-w-none dark:prose-invert"
    >
      {content}
    </ReactMarkdown>
  )
}