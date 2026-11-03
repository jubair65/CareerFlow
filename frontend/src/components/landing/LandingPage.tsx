import { useEffect, useRef } from 'react';
import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { LandingHeader } from './LandingHeader';
import { LandingHero } from './LandingHero';
import { CandidatePinnedScene } from './CandidatePinnedScene';
import { HiringLeaderboardScene } from './HiringLeaderboardScene';
import { AgencyPipelineScene } from './AgencyPipelineScene';
import { TrustBand } from './TrustBand';
import { LandingFooter } from './LandingFooter';

gsap.registerPlugin(ScrollTrigger);

export function LandingPage() {
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    // Check user preference for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    // Initialize Lenis for smooth scroll
    const lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 0.9,
    });
    lenisRef.current = lenis;

    // Connect Lenis to GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update);

    const tickerCb = (time: number) => {
      lenis.raf(time * 1000);
    };

    gsap.ticker.add(tickerCb);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(tickerCb);
      lenis.destroy();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  const scrollToTop = () => {
    if (lenisRef.current) {
      lenisRef.current.scrollTo(0, { duration: 1.2 });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div
      className="cf-shell cf-noise w-full bg-[#f5f1e6] text-[#253142]"
      style={{
        backgroundColor: 'var(--cf-landing-light, #f5f1e6)',
        borderTop: 'none',
        margin: 0,
        padding: 0,
      }}
    >
      <LandingHeader onLogoClick={scrollToTop} />

      <main id="main-content">
        <LandingHero />
        <CandidatePinnedScene />
        <HiringLeaderboardScene />
        <AgencyPipelineScene />
        <TrustBand />
      </main>

      <LandingFooter />
    </div>
  );
}

export default LandingPage;

