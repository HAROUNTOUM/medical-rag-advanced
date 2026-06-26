import { NextRequest, NextResponse } from "next/server";

/**
 * Auth Guard Middleware — protects all /dashboard/* routes.
 * Redirects to /login if no Bearer token is found in localStorage (via cookie fallback).
 * The actual JWT validity is enforced by the FastAPI backend on every API call.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protect dashboard routes
  if (pathname.startsWith("/dashboard")) {
    // Check for token in cookie (set by login page for middleware access)
    const token = request.cookies.get("auth_token")?.value;

    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("from", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Redirect authenticated users away from login/register
  if (pathname === "/login" || pathname === "/register") {
    const token = request.cookies.get("auth_token")?.value;
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/register"],
};
