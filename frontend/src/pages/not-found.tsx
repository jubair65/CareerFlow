import { Card, CardContent } from '@/components/ui/card';
import { AlertCircle, ArrowLeft } from 'lucide-react';
import { Logo } from '../components/brand/Logo';
import { useLocation } from 'wouter';

export default function NotFound() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-[#f5f1e6] p-4 text-[#253142]">
      <div className="mb-8">
        <Logo tone="color" size="lg" onClick={() => setLocation('/')} />
      </div>

      <Card className="w-full max-w-md mx-4 rounded-3xl border border-[#d9dbd1] bg-white shadow-xl">
        <CardContent className="p-8 text-center space-y-4">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#fee2e2] text-[#dc2626]">
            <AlertCircle className="h-7 w-7" />
          </div>

          <h1 className="cf-display text-2xl font-bold text-[#253142]">
            404 Page Not Found
          </h1>

          <p className="text-sm text-[#687382] leading-relaxed">
            The page you are looking for does not exist or may have been moved.
          </p>

          <div className="pt-2">
            <button
              onClick={() => setLocation('/')}
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition cursor-pointer"
            >
              <ArrowLeft size={14} /> Back to CareerFlow
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
