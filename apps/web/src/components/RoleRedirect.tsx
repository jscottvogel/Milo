"use client";

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAppStore } from '@/store/useAppStore';

export function RoleRedirect() {
  const { userRole } = useAppStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Only redirect if we are on the root or home page, to avoid redirect loops
    if (pathname === '/' || pathname === '/home') {
      if (userRole === 'Engineer' || userRole === 'PM') {
        router.push('/programs');
      } else if (userRole === 'Finance') {
        router.push('/programs/financials');
      }
    }
  }, [userRole, pathname, router]);

  return null;
}
