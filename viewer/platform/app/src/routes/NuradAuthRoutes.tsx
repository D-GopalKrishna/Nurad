import React, { useEffect } from 'react';
import { Route, Routes } from 'react-router-dom';
import NuradLogin from './NuradLogin/NuradLogin';

const TOKEN_STORAGE_KEY = 'ohif-auth-token';

/**
 * Simple username/password auth gate for OHIF, replacing the need to bounce
 * through the separate 5173 worklist app to get a JWT into the viewer.
 * Modeled on OpenIdConnectRoutes.tsx, but for plain Django JWT login instead
 * of OIDC. See .vscode/plan/03-ohif-native-login.md.
 */
function NuradAuthRoutes({ userAuthenticationService }) {
  useEffect(() => {
    userAuthenticationService.setServiceImplementation({
      // PrivateRoute (routes/index.tsx) calls this synchronously from inside
      // another component's render, not from an effect/event handler - React
      // Router's navigate() is invalid there and gets silently dropped. Use a
      // hard redirect instead, same as OpenIdConnectRoutes.tsx's
      // handleUnauthenticated (userManager.signinRedirect()) does.
      handleUnauthenticated: () => {
        window.location.assign('/login');
        return null;
      },
    });

    // Restore a session that already has a token (e.g. a page refresh) so
    // the enabled:true below doesn't immediately bounce a logged-in user.
    const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      userAuthenticationService.setServiceImplementation({
        getAuthorizationHeader: () => ({ Authorization: 'Bearer ' + token }),
      });
      userAuthenticationService.setUser({ token });
    }

    userAuthenticationService.set({ enabled: true });
  }, []);

  return (
    <Routes>
      <Route
        path="/login"
        element={<NuradLogin userAuthenticationService={userAuthenticationService} />}
      />
    </Routes>
  );
}

export default NuradAuthRoutes;
