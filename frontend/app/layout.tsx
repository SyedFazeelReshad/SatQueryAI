import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from 'react-hot-toast';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SatQuery AI | Remote Sensing Intelligence',
  description: 'Understand Earth from every signal with natural language querying of satellite imagery.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-background text-slate-900 min-h-screen flex flex-col`}>
        {children}
        <Toaster position="bottom-right" toastOptions={{
          style: {
            background: '#ffffff',
            color: '#0f172a',
            border: '1px solid #e2e8f0',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }
        }}/>
      </body>
    </html>

  );
}
