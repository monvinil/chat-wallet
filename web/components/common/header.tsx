'use client';

import Link from 'next/link';
import { CircleDollarSign } from 'lucide-react';

interface HeaderProps {
  title?: string;
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden">
      <Link href="/wallet" className="flex items-center gap-2">
        <CircleDollarSign className="h-7 w-7 text-primary" />
        <span className="text-lg font-bold">{title || 'USDChat'}</span>
      </Link>
    </header>
  );
}
