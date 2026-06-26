"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { Book, MessageSquare, LogOut, Menu, User, Key } from "lucide-react";
import Breadcrumb from "@/components/ui/breadcrumb";
import { api } from "@/lib/api";

interface DoctorProfile {
  id: number;
  email: string;
  full_name: string | null;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [doctor, setDoctor] = useState<DoctorProfile | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    // Load doctor profile
    api
      .get("/api/v1/auth/me")
      .then((data) => setDoctor(data))
      .catch(() => {
        // Token invalid — force logout
        handleLogout();
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    // Clear cookie
    document.cookie = "auth_token=; path=/; max-age=0";
    router.push("/login");
  };

  const navigation = [
    { name: "Knowledge Base", href: "/dashboard/knowledge", icon: Book },
    { name: "Chat", href: "/dashboard/chat", icon: MessageSquare },
    { name: "API Keys", href: "/dashboard/api-keys", icon: Key },
  ];

  const initials = doctor?.full_name
    ? doctor.full_name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : doctor?.email?.slice(0, 2).toUpperCase() ?? "DR";

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-0 left-0 m-4 z-50">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-md bg-primary text-primary-foreground"
        >
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-card border-r transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          {/* Sidebar header */}
          <div className="flex h-20 items-center border-b pl-4 pr-4 bg-gradient-to-r from-blue-50 to-blue-100">
            <Link
              href="/dashboard"
              className="flex items-center gap-3 hover:opacity-80 transition-opacity w-full"
            >
              <img
                src="/doctome-logo.png"
                alt="RADOCT Logo"
                className="h-12 w-auto"
              />
              <div className="flex flex-col leading-none">
                <span className="text-lg font-bold text-blue-600">RADOCT</span>
                <span className="text-xs text-blue-500 font-medium">Healthcare Platform</span>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-6">
            {navigation.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? "bg-primary/15 text-primary border-l-4 border-primary font-semibold"
                      : "text-slate-600 hover:bg-slate-100/50 hover:text-slate-900"
                  }`}
                >
                  <item.icon
                    className={`mr-3 h-5 w-5 transition-all duration-200 ${
                      isActive
                        ? "text-primary scale-110"
                        : "text-slate-500 group-hover:text-slate-700 group-hover:scale-110"
                    }`}
                  />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Doctor profile + logout */}
          <div className="border-t border-slate-200 p-4 space-y-3">
            {doctor && (
              <div className="flex items-center gap-3 px-1">
                <div className="h-9 w-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm flex-shrink-0">
                  {initials}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800 truncate">
                    {doctor.full_name ?? "Doctor"}
                  </p>
                  <p className="text-xs text-slate-500 truncate">{doctor.email}</p>
                </div>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-700 transition-colors duration-200"
            >
              <LogOut className="mr-3 h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="min-h-screen py-6 px-4 sm:px-6 lg:px-8">
          <Breadcrumb />
          {children}
        </main>
      </div>
    </div>
  );
}

export const dashboardConfig = {
  mainNav: [],
  sidebarNav: [
    { title: "Knowledge Base", href: "/dashboard/knowledge", icon: "database" },
    { title: "Chat", href: "/dashboard/chat", icon: "messageSquare" },
    { title: "API Keys", href: "/dashboard/api-keys", icon: "key" },
  ],
};
