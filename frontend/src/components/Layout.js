import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MEDIA, ORG_INFO } from "../data/missions";
import { Menu, X, Globe, Mail, Phone, MapPin, Users, User, Ticket } from "lucide-react";
import { Button } from "../components/ui/button";

export function Header() {
  const { user, logout } = useAuth();
  const { lang, toggle } = useLang();
  const t = translations[lang].nav;
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { to: "/", label: t.home },
    { to: "/about", label: t.about },
    { to: "/missions", label: t.missions },
    { to: "/wall-of-fame", label: lang === "hi" ? "गौरव पट" : "Wall of Fame" },
    { to: "/volunteer", label: t.volunteer },
    { to: "/contact", label: t.contact },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="fixed top-0 w-full z-50 glass-header bg-gradient-to-r from-[#C8F2CE]/80 via-[#A7D9E8]/80 to-[#91C8E7]/80 border-b border-[#91C8E7]/30" data-testid="main-header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          <Link to="/" className="flex items-center gap-3 shrink-0" data-testid="header-logo-link">
            <img src={MEDIA.logo} alt="Heroic HIFI Foundation Logo" className="h-12 sm:h-14 w-auto rounded-lg" />
            <div className="hidden sm:block">
              <span className="text-sm font-semibold text-[#1E3A8A] tracking-wide" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                HEROIC HIFI
              </span>
              <span className="block text-[10px] text-stone-500 tracking-widest uppercase">Foundation</span>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-1" data-testid="desktop-nav">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`px-3 py-2 rounded-full text-sm font-medium transition-colors duration-200 ${
                  isActive(link.to)
                    ? "bg-[#28A9E2]/10 text-[#1E56A0]"
                    : "text-slate-600 hover:text-[#1E56A0] hover:bg-[#28A9E2]/5"
                }`}
                data-testid={`nav-${link.to.replace("/", "") || "home"}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={toggle}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-[#28A9E2]/20 text-[#1E56A0] hover:bg-[#28A9E2]/5 transition-colors"
              data-testid="language-toggle"
            >
              <Globe className="w-3.5 h-3.5" />
              {lang === "en" ? "HI" : "EN"}
            </button>

            {user ? (
              <>
                <Link to="/community">
                  <Button variant="ghost" size="sm" className="text-sm hidden sm:inline-flex gap-1" data-testid="nav-community">
                    <Users className="w-4 h-4" />
                    {t.community}
                  </Button>
                </Link>
                <Link to="/profile">
                  <Button variant="ghost" size="sm" className="text-sm hidden sm:inline-flex gap-1" data-testid="nav-profile">
                    <User className="w-4 h-4" />
                    {lang === "hi" ? "प्रोफ़ाइल" : "Profile"}
                  </Button>
                </Link>
                <Link to="/dashboard">
                  <Button variant="ghost" size="sm" className="text-sm hidden sm:inline-flex" data-testid="nav-dashboard">
                    {t.dashboard}
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" onClick={logout} className="text-sm hidden sm:inline-flex" data-testid="logout-btn">
                  {t.logout}
                </Button>
              </>
            ) : (
              <Link to="/login" className="hidden sm:inline-flex">
                <Button variant="ghost" size="sm" className="text-sm" data-testid="nav-login">
                  {t.login}
                </Button>
              </Link>
            )}

            <Link to="/donate">
              <Button
                className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-4 sm:px-6 py-2 text-sm font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
                data-testid="nav-donate-cta"
              >
                {t.donate_now}
              </Button>
            </Link>

            <button
              className="lg:hidden p-2 text-[#1E56A0]"
              onClick={() => setMobileOpen(!mobileOpen)}
              data-testid="mobile-menu-toggle"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden bg-gradient-to-r from-[#C8F2CE]/95 via-[#A7D9E8]/95 to-[#91C8E7]/95 backdrop-blur-xl border-t border-[#91C8E7]/20 py-4 px-4" data-testid="mobile-menu">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setMobileOpen(false)}
              className={`block py-3 px-4 rounded-xl text-sm font-medium ${
                isActive(link.to) ? "bg-[#28A9E2]/10 text-[#1E56A0]" : "text-slate-600"
              }`}
            >
              {link.label}
            </Link>
          ))}
          {user ? (
            <>
              <Link to="/community" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-3 px-4 text-sm text-slate-600" data-testid="mobile-nav-community">
                <Users className="w-4 h-4" />
                {t.community}
              </Link>
              <Link to="/profile" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-3 px-4 text-sm text-slate-600" data-testid="mobile-nav-profile">
                <User className="w-4 h-4" />
                {lang === "hi" ? "प्रोफ़ाइल" : "Profile"}
              </Link>
              <Link to="/tickets" onClick={() => setMobileOpen(false)} className="flex items-center gap-2 py-3 px-4 text-sm text-slate-600" data-testid="mobile-nav-tickets">
                <Ticket className="w-4 h-4" />
                {lang === "hi" ? "शिकायत" : "Tickets"}
              </Link>
              <Link to="/dashboard" onClick={() => setMobileOpen(false)} className="block py-3 px-4 text-sm text-slate-600">{t.dashboard}</Link>
              <button onClick={() => { logout(); setMobileOpen(false); }} className="block py-3 px-4 text-sm text-slate-600 w-full text-left">{t.logout}</button>
            </>
          ) : (
            <Link to="/login" onClick={() => setMobileOpen(false)} className="block py-3 px-4 text-sm text-slate-600">{t.login}</Link>
          )}
        </div>
      )}
    </header>
  );
}

export function Footer() {
  const { lang } = useLang();
  const t = translations[lang].footer;
  const tNav = translations[lang].nav;

  return (
    <footer className="bg-[#0D2847] text-blue-100/70 mt-auto" data-testid="main-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          <div className="lg:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <img src={MEDIA.logo} alt="Logo" className="h-14 w-auto rounded-lg" />
              <div>
                <span className="text-white font-semibold text-lg" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                  HEROIC HIFI
                </span>
                <span className="block text-xs text-[#28A9E2] tracking-widest uppercase">Foundation</span>
              </div>
            </div>
            <p className="text-sm text-blue-200/60 leading-relaxed">{t.tagline}</p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">{t.quick_links}</h4>
            <div className="space-y-2">
              {[
                { to: "/about", label: tNav.about },
                { to: "/missions", label: tNav.missions },
                { to: "/donate", label: tNav.donate },
                { to: "/volunteer", label: tNav.volunteer },
                { to: "/contact", label: tNav.contact },
              ].map((l) => (
                <Link key={l.to} to={l.to} className="block text-sm text-blue-200/60 hover:text-[#28A9E2] transition-colors">{l.label}</Link>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">{t.connect}</h4>
            <div className="space-y-3">
              <a href={`mailto:${ORG_INFO.email}`} className="flex items-center gap-2 text-sm text-blue-200/60 hover:text-[#28A9E2] transition-colors">
                <Mail className="w-4 h-4" /> {ORG_INFO.email}
              </a>
              <a href={`tel:${ORG_INFO.phone}`} className="flex items-center gap-2 text-sm text-blue-200/60 hover:text-[#28A9E2] transition-colors">
                <Phone className="w-4 h-4" /> {ORG_INFO.phone}
              </a>
              <div className="flex items-start gap-2 text-sm text-blue-200/60">
                <MapPin className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{ORG_INFO.address}</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">{t.legal}</h4>
            <div className="space-y-2 text-sm text-blue-200/60">
              <p><span className="text-blue-300/50">{t.cin}:</span> {ORG_INFO.cin}</p>
              <p>{t.section8}</p>
            </div>
          </div>
        </div>

        <div className="border-t border-blue-900/40 mt-12 pt-8 text-center text-sm text-blue-300/40">
          &copy; {new Date().getFullYear()} {ORG_INFO.name}. {t.rights}
        </div>
      </div>
    </footer>
  );
}

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#E4F5E7] via-[#D6EBF2] to-[#CBE4F3]">
      <Header />
      <main className="flex-1 pt-16 sm:pt-20">
        {children}
      </main>
      <Footer />
    </div>
  );
}
