import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function MPGroundwaterIndex() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the well list page (main app page)
    router.replace('/well');
  }, [router]);

  return null;
}
