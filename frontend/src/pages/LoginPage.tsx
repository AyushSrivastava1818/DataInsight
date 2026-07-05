import React, { useState } from 'react';
import { useAuth, supabase } from '../components/Shared/AuthContext';
import { GlassCard } from '../components/UI/GlassCard';
import { LogIn, Sparkles, AlertCircle, Chrome } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { loginWithGoogle } = useAuth();
  const [isSignUp, setIsSignUp] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      setError("Auth services are currently offline. Check environment settings.");
      return;
    }
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      if (isSignUp) {
        const { error: signUpErr } = await supabase.auth.signUp({
          email,
          password
        });
        if (signUpErr) throw signUpErr;
        setMessage("Verification email sent! Check your inbox.");
      } else {
        const { error: signInErr } = await supabase.auth.signInWithPassword({
          email,
          password
        });
        if (signInErr) throw signInErr;
      }
    } catch (err: any) {
      setError(err.message || 'Authentication operation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    try {
      await loginWithGoogle();
    } catch (err: any) {
      setError(err.message || 'Failed to initiate Google sign in.');
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 px-6 py-12">
      <div className="w-full max-w-md space-y-6 fade-in">
        
        {/* Brand/Logo Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3.5 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-3xl text-white shadow-xl shadow-brand-500/20 mb-2 border border-white/10">
            <Sparkles className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">DataInsight AI</h1>
          <p className="text-slate-400 text-sm">Deploy premium statistical cleaning & profiling workstation</p>
        </div>

        {/* Auth Glass Card */}
        <GlassCard className="p-8 border-white/5 bg-slate-950/40 backdrop-blur-md">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <LogIn className="w-5 h-5 text-brand-500" /> {isSignUp ? 'Create your Account' : 'Welcome back'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-500 text-xs font-semibold">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{error}</p>
              </div>
            )}

            {message && (
              <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-500 text-xs font-semibold">
                <Sparkles className="w-4 h-4 shrink-0" />
                <p>{message}</p>
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-slate-900/50 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-white rounded-xl py-3 px-4 text-sm transition-all outline-none"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900/50 border border-slate-800 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-white rounded-xl py-3 px-4 text-sm transition-all outline-none"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 mt-2 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-brand-500/10 hover:shadow-brand-500/25 flex items-center justify-center gap-2"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : isSignUp ? (
                'Sign Up'
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Social Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-950/10 px-3 text-slate-500 font-bold">Or continue with</span>
            </div>
          </div>

          {/* Social login buttons */}
          <button
            onClick={handleGoogleLogin}
            className="w-full py-3 bg-slate-900 hover:bg-slate-850 text-slate-300 border border-slate-800 hover:border-slate-700 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2"
          >
            <Chrome className="w-4 h-4 text-rose-500" /> Sign in with Google
          </button>

          {/* Switch Modes */}
          <p className="text-center text-xs text-slate-500 mt-6 font-medium">
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError(null);
                setMessage(null);
              }}
              className="text-brand-500 hover:underline font-bold"
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </GlassCard>
        
      </div>
    </div>
  );
};
