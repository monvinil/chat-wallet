'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface NavLinkProps {
  href: string;
  icon: LucideIcon;
  label: string;
  className?: string;
}

export function NavLink({ href, icon: Icon, label, className }: NavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
        className
      )}
    >
      <Icon className="h-5 w-5" />
      <span>{label}</span>
    </Link>
  );
}

interface BottomNavLinkProps {
  href: string;
  icon: LucideIcon;
  label: string;
}

export function BottomNavLink({ href, icon: Icon, label }: BottomNavLinkProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        'flex flex-col items-center justify-center gap-1 py-2 text-xs font-medium transition-colors',
        isActive
          ? 'text-primary'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      <Icon className={cn('h-5 w-5', isActive && 'text-primary')} />
      <span>{label}</span>
    </Link>
  );
}
