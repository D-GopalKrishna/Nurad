import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppConfig } from '@state';

const TOKEN_STORAGE_KEY = 'ohif-auth-token';
const LOGIN_URL = 'http://localhost:8000/api/auth/login/';

export default function NuradLogin({ userAuthenticationService }) {
  const [appConfig] = useAppConfig();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const logoComponent = appConfig?.whiteLabeling?.createLogoComponentFn?.(React) ?? null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await fetch(LOGIN_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid username or password');
      }

      const data = await response.json();
      const token = data.access;

      sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
      userAuthenticationService.setServiceImplementation({
        getAuthorizationHeader: () => ({ Authorization: 'Bearer ' + token }),
      });
      userAuthenticationService.setUser({ username });

      navigate('/');
    } catch {
      setError('Invalid username or password');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="bg-background flex min-h-screen items-center justify-center px-4">
      <div className="bg-card border-border w-full max-w-sm rounded-xl border p-8 shadow-lg">
        <div className="mb-6 flex flex-col items-center gap-3 text-center">
          {logoComponent}
          <div>
            <h1 className="text-card-foreground text-xl font-bold">Sign in to Nurad</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Welcome back — sign in to view and review studies.
            </p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4"
        >
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="username"
              className="text-card-foreground text-sm font-medium"
            >
              Username
            </label>
            <input
              id="username"
              autoFocus
              placeholder="Enter your username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="bg-input/30 border-input text-foreground placeholder:text-muted-foreground focus:ring-ring rounded-md border px-3 py-2 text-sm outline-none focus:ring-2"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="password"
              className="text-card-foreground text-sm font-medium"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="bg-input/30 border-input text-foreground placeholder:text-muted-foreground focus:ring-ring rounded-md border px-3 py-2 text-sm outline-none focus:ring-2"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-primary text-primary-foreground hover:bg-primary/90 mt-2 rounded-md px-3 py-2 text-sm font-semibold disabled:opacity-60"
          >
            {isSubmitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
