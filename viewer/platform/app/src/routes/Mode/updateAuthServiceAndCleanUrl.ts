const STORAGE_KEY = 'ohif-auth-token';

/**
 * Updates the user authentication service with the provided token and cleans the token from the URL.
 *
 * If no token is passed (e.g. on a page refresh, after a previous call already
 * stripped it from the URL), falls back to the token persisted in
 * sessionStorage by an earlier call, so the auth header survives a refresh
 * for the lifetime of the tab.
 *
 * @param token - The token to set in the user authentication service, or undefined/null to fall back to storage.
 * @param location - The location object from the router.
 * @param userAuthenticationService - The user authentication service instance.
 */
export function updateAuthServiceAndCleanUrl(
  token: string,
  location: any,
  userAuthenticationService: any
): void {
  const effectiveToken = token || sessionStorage.getItem(STORAGE_KEY);

  if (!effectiveToken) {
    return;
  }

  if (token) {
    sessionStorage.setItem(STORAGE_KEY, token);
  }

  // set the userAuthenticationService to use the token for the
  // Authorization header for all requests
  userAuthenticationService.setServiceImplementation({
    getAuthorizationHeader: () => ({
      Authorization: 'Bearer ' + effectiveToken,
    }),
  });

  if (!token) {
    // Token came from storage, not the URL - nothing to clean up.
    return;
  }

  // Create a URL object with the current location
  const urlObj = new URL(window.location.origin + window.location.pathname + location.search);

  // Remove the token from the URL object
  urlObj.searchParams.delete('token');
  const cleanUrl = urlObj.toString();

  // Update the browser's history without the token
  if (window.history && window.history.replaceState) {
    window.history.replaceState(null, '', cleanUrl);
  }
}
