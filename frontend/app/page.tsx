"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!loading && user) {
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-cyan-400 font-mono text-xl animate-pulse">
          LOADING...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 opacity-10">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 217, 255, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 217, 255, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
        />
      </div>

      {/* Navigation Bar */}
      <nav className="relative z-50 border-b border-cyan-400/20 bg-black/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-cyan-400 font-mono tracking-widest">
                J.A.R.V.I.S
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login">
                <Button className="bg-cyan-500/20 border border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-24 lg:py-32">
          <div className="text-center">
            {/* Main Heading */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6">
              <span className="text-cyan-400 font-mono tracking-widest">
                J.A.R.V.I.S
              </span>
              <br />
              <span className="text-white">AI Assistant</span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl sm:text-2xl text-cyan-300/80 mb-8 max-w-3xl mx-auto font-mono">
              Your intelligent voice-activated assistant powered by advanced AI.
              Manage your calendar, send emails, search the web, and more.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              <Link href="/login">
                <Button
                  size="lg"
                  className="bg-cyan-500/20 border-2 border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono text-lg px-8 py-6 glow-box"
                >
                  Get Started
                </Button>
              </Link>
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-cyan-400/50 text-cyan-300 hover:bg-cyan-500/10 font-mono text-lg px-8 py-6"
                onClick={() => {
                  document
                    .getElementById("features")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
              >
                Learn More
              </Button>
            </div>

            {/* Visual Element - Jarvis Core Preview */}
            <div className="flex justify-center mb-20">
              <div className="relative w-64 h-64 sm:w-80 sm:h-80">
                <div className="absolute inset-0 rounded-full bg-gradient-to-b from-cyan-500/30 to-blue-600/20 blur-3xl opacity-60" />
                <div className="absolute inset-0 rounded-full border-4 border-cyan-400/50 animate-pulse" />
                <div className="absolute inset-4 rounded-full border-2 border-cyan-400/30" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-cyan-400 tracking-widest font-mono mb-2">
                      J.A.R.V.I.S
                    </div>
                    <div className="h-0.5 w-32 mx-auto bg-gradient-to-r from-transparent via-cyan-400 to-transparent" />
                    <div className="text-xs text-cyan-400/60 font-mono mt-2">
                      ACTIVE
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <section
          id="features"
          className="py-20 sm:py-24 lg:py-32 border-t border-cyan-400/20"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-4xl font-bold text-center mb-12 text-cyan-400 font-mono">
              FEATURES
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {/* Feature 1 */}
              <div className="bg-black/50 border border-cyan-400/20 rounded-lg p-6 hover:border-cyan-400/50 transition-all glow-box">
                <div className="text-4xl mb-4">🎤</div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2 font-mono">
                  Voice Interface
                </h3>
                <p className="text-cyan-300/70 text-sm">
                  Natural voice interaction with real-time AI responses
                </p>
              </div>

              {/* Feature 2 */}
              <div className="bg-black/50 border border-cyan-400/20 rounded-lg p-6 hover:border-cyan-400/50 transition-all glow-box">
                <div className="text-4xl mb-4">📅</div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2 font-mono">
                  Calendar Management
                </h3>
                <p className="text-cyan-300/70 text-sm">
                  Schedule and manage events with Google Calendar integration
                </p>
              </div>

              {/* Feature 3 */}
              <div className="bg-black/50 border border-cyan-400/20 rounded-lg p-6 hover:border-cyan-400/50 transition-all glow-box">
                <div className="text-4xl mb-4">📧</div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2 font-mono">
                  Email Control
                </h3>
                <p className="text-cyan-300/70 text-sm">
                  Send and manage emails through voice commands
                </p>
              </div>

              {/* Feature 4 */}
              <div className="bg-black/50 border border-cyan-400/20 rounded-lg p-6 hover:border-cyan-400/50 transition-all glow-box">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-xl font-bold text-cyan-400 mb-2 font-mono">
                  Web Search
                </h3>
                <p className="text-cyan-300/70 text-sm">
                  Search the web and get instant information
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 sm:py-24 lg:py-32 border-t border-cyan-400/20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold mb-6 text-cyan-400 font-mono">
              READY TO GET STARTED?
            </h2>
            <p className="text-xl text-cyan-300/80 mb-8 font-mono">
              Experience the future of AI assistance. Sign in to access your
              personal JARVIS dashboard.
            </p>
            <Link href="/login">
              <Button
                size="lg"
                className="bg-cyan-500/20 border-2 border-cyan-400 text-cyan-300 hover:bg-cyan-500/30 font-mono text-lg px-8 py-6 glow-box"
              >
                Access Dashboard
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-cyan-400/20 bg-black/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h3 className="text-xl font-bold text-cyan-400 font-mono tracking-widest">
                J.A.R.V.I.S
              </h3>
              <p className="text-cyan-300/60 text-sm font-mono mt-2">
                AI Assistant Platform
              </p>
            </div>
            <div className="flex gap-6 text-sm text-cyan-300/60 font-mono">
              <a href="#" className="hover:text-cyan-400 transition-colors">
                Privacy
              </a>
              <a href="#" className="hover:text-cyan-400 transition-colors">
                Terms
              </a>
              <a href="#" className="hover:text-cyan-400 transition-colors">
                Contact
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-cyan-400/10 text-center text-cyan-300/40 text-sm font-mono">
            <p>
              © {new Date().getFullYear()} JARVIS AI Assistant. All rights
              reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
