# Gemini Web Wrapper Frontend

A modern Next.js frontend for the Gemini Web Wrapper API, featuring a beautiful chat interface with all the functionality of the original web wrapper.

## Features

- 🎨 **Modern UI**: Clean, responsive design with dark/light mode support
- 💬 **Real-time Chat**: Live messaging with Gemini AI
- 📋 **Chat Management**: Create, delete, and manage multiple chat sessions
- 🔧 **Chat Modes**: Switch between different conversation modes (Code, Architect, Debug, etc.)
- 📝 **Markdown Support**: Rich text rendering with syntax highlighting
- ⚡ **Fast Performance**: Built with Next.js 14 and optimized for speed
- 🎯 **TypeScript**: Full type safety throughout the application

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + Custom components
- **State Management**: Zustand
- **Markdown**: React Markdown + Syntax Highlighter
- **Icons**: Lucide React
- **Notifications**: React Hot Toast

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Running Gemini Web Wrapper API (backend)

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

2. **Set up environment variables**:
   Create a `.env.local` file in the frontend directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open your browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Development

### Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js app directory
│   │   ├── globals.css      # Global styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main page
│   ├── components/          # React components
│   │   ├── ui/             # Reusable UI components
│   │   ├── chat-interface.tsx
│   │   ├── sidebar.tsx
│   │   ├── message-content.tsx
│   │   ├── create-chat-dialog.tsx
│   │   └── chat-mode-dialog.tsx
│   ├── lib/                # Utility functions
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helper functions
│   ├── store/              # State management
│   │   └── chat-store.ts   # Zustand store
│   └── types/              # TypeScript types
│       └── index.ts
├── public/                 # Static assets
└── package.json
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Key Components

#### ChatInterface
The main chat component that handles:
- Message display and input
- Real-time typing indicators
- Auto-scrolling to new messages
- Message submission

#### Sidebar
Manages chat sessions:
- Chat list display
- Create new chats
- Delete chats
- Change chat modes
- Set active chat

#### MessageContent
Renders message content with:
- Markdown support
- Syntax highlighting for code blocks
- Responsive design

## API Integration

The frontend communicates with the Gemini Web Wrapper API through the `/api` client in `src/lib/api.ts`. All API calls are proxied through Next.js API routes to avoid CORS issues.

### Supported Endpoints

- `GET /api/chats` - List all chats
- `POST /api/chats` - Create new chat
- `DELETE /api/chats/{id}` - Delete chat
- `PUT /api/chats/{id}/mode` - Update chat mode
- `POST /api/chats/active` - Set active chat
- `GET /api/chats/active` - Get active chat
- `POST /api/chat/completions` - Send message

## Styling

The project uses Tailwind CSS with a custom design system:

- **Colors**: CSS custom properties for theming
- **Components**: Reusable UI components with variants
- **Animations**: Smooth transitions and micro-interactions
- **Responsive**: Mobile-first design approach

## State Management

Zustand is used for state management with the following stores:

- **Chat Store**: Manages chat sessions, messages, and API interactions
- **UI Store**: Handles UI state like dialogs and loading states

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Connection Error**:
   - Ensure the backend API is running on the correct port
   - Check the `NEXT_PUBLIC_API_URL` environment variable

2. **Build Errors**:
   - Clear `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `npm install`

3. **TypeScript Errors**:
   - Run `npm run lint` to check for issues
   - Ensure all types are properly imported

## License

This project is part of the Gemini Web Wrapper and follows the same license.