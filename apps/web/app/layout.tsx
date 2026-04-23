export const metadata = { title: 'NCEC Enricher' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'Arial, sans-serif', margin: 0, padding: 24, background: '#f7f7f7' }}>{children}</body>
    </html>
  );
}
