import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MEDIA, MISSIONS_CLIENT } from "../data/missions";
import { Button } from "../components/ui/button";
import { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt, Droplets, ChefHat, ArrowRight, Gift, Umbrella, Flower2, Trophy, Award, UserPlus, Compass, Star } from "lucide-react";
import Marquee from "react-fast-marquee";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import api from "../lib/api";

const iconMap = { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt };

function HeroSection() {
  const { lang } = useLang();
  const t = translations[lang].hero;

  return (
    <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden" data-testid="hero-section">
      <div className="absolute inset-0">
        <img src={MEDIA.hero_main} alt="Heroic HIFI Foundation" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/65 via-black/45 to-black/70" />
      </div>
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <motion.p
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-[#FF7F00] mb-6"
        >
          {t.overline}
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
          className="text-4xl sm:text-5xl lg:text-7xl font-semibold tracking-tight leading-none text-white mb-6"
          style={{ fontFamily: "'Cormorant Garamond', serif" }}
        >
          {t.title}
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
          className="text-base sm:text-lg text-stone-200 leading-relaxed max-w-2xl mx-auto mb-10"
        >
          {t.subtitle}
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <Link to="/donate">
            <Button className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-8 py-3 text-base font-medium shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-200" data-testid="hero-donate-btn">
              {t.cta_donate}
            </Button>
          </Link>
          <Link to="/missions">
            <Button variant="outline" className="border-white/30 text-white hover:bg-white/10 rounded-full px-8 py-3 text-base font-medium backdrop-blur-sm" data-testid="hero-missions-btn">
              {t.cta_missions} <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

function MissionsMarquee() {
  return (
    <div className="bg-gradient-to-r from-[#C8F2CE]/40 via-[#A7D9E8]/40 to-[#91C8E7]/40 py-4 border-y border-[#91C8E7]/20" data-testid="missions-marquee">
      <Marquee speed={40} gradient={false} pauseOnHover>
        {MISSIONS_CLIENT.map((m) => (
          <span key={m.slug} className="marquee-item">
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: m.color }} />
            {m.name}
          </span>
        ))}
      </Marquee>
    </div>
  );
}

function MissionsGrid() {
  const { lang } = useLang();
  const t = translations[lang].home;

  return (
    <section className="py-20 sm:py-28" data-testid="missions-grid-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-[#FF7F00] mb-3">{t.missions_subtitle}</p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.missions_title}
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {MISSIONS_CLIENT.map((mission, i) => {
            const Icon = iconMap[mission.icon];
            return (
              <motion.div
                key={mission.slug}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: i * 0.08 }}
                className={`mission-card-hover ${i === 0 ? "sm:col-span-2 lg:col-span-2 lg:row-span-2" : ""}`}
              >
                <Link to={`/missions/${mission.slug}`} className="block h-full" data-testid={`mission-card-${mission.slug}`}>
                  <div className="relative h-full min-h-[280px] rounded-2xl overflow-hidden group">
                    <img
                      src={mission.image}
                      alt={mission.name}
                      className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
                    <div className="absolute bottom-0 left-0 right-0 p-6 sm:p-8">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: mission.color }}>
                          {Icon && <Icon className="w-4 h-4 text-white" />}
                        </div>
                        <span className="text-xs uppercase tracking-wider text-white/80 font-medium">
                          {lang === "hi" ? mission.name_hi : mission.name}
                        </span>
                      </div>
                      <p className="text-white text-sm sm:text-base leading-relaxed">
                        {lang === "hi" ? mission.tagline_hi : mission.tagline}
                      </p>
                    </div>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function DrivesSection() {
  const { lang } = useLang();
  const t = translations[lang].home;

  return (
    <section className="py-20 bg-gradient-to-r from-[#C8F2CE]/30 via-[#A7D9E8]/30 to-[#91C8E7]/30" data-testid="drives-section">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <p className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-[#16A34A] mb-3">{t.drives_subtitle}</p>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#1C1917]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.drives_title}
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}
            className="bg-white rounded-2xl p-8 shadow-sm border border-sky-100 hover:shadow-md transition-shadow"
            data-testid="blood-donation-card"
          >
            <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center mb-6">
              <Droplets className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-xl sm:text-2xl font-medium text-[#0D2847] mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.blood_title}</h3>
            <p className="text-sm sm:text-base text-slate-500 leading-relaxed">{t.blood_desc}</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}
            className="bg-white rounded-2xl p-8 shadow-sm border border-sky-100 hover:shadow-md transition-shadow"
            data-testid="langar-card"
          >
            <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center mb-6">
              <ChefHat className="w-6 h-6 text-[#FF7F00]" />
            </div>
            <h3 className="text-xl sm:text-2xl font-medium text-[#0D2847] mb-3" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.langar_title}</h3>
            <p className="text-sm sm:text-base text-slate-500 leading-relaxed">{t.langar_desc}</p>
          </motion.div>
        </div>

        <div className="mt-12">
          <p className="text-center text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-[#1E56A0] mb-8">{t.custom_drives_title}</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-sky-100 hover:shadow-md transition-shadow text-center" data-testid="birthday-drive-card">
              <div className="w-10 h-10 rounded-xl bg-pink-50 flex items-center justify-center mx-auto mb-4">
                <Gift className="w-5 h-5 text-pink-500" />
              </div>
              <h4 className="text-base font-medium text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.birthday_title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{t.birthday_desc}</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-sky-100 hover:shadow-md transition-shadow text-center" data-testid="memorial-drive-card">
              <div className="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center mx-auto mb-4">
                <Flower2 className="w-5 h-5 text-violet-500" />
              </div>
              <h4 className="text-base font-medium text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.memorial_title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{t.memorial_desc}</p>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-sky-100 hover:shadow-md transition-shadow text-center" data-testid="seasonal-drive-card">
              <div className="w-10 h-10 rounded-xl bg-cyan-50 flex items-center justify-center mx-auto mb-4">
                <Umbrella className="w-5 h-5 text-cyan-600" />
              </div>
              <h4 className="text-base font-medium text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{t.seasonal_title}</h4>
              <p className="text-xs text-slate-500 leading-relaxed">{t.seasonal_desc}</p>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  const { lang } = useLang();
  const t = translations[lang].home;

  return (
    <section className="py-20 sm:py-28" data-testid="cta-section">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
          className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#0D2847] mb-4"
          style={{ fontFamily: "'Cormorant Garamond', serif" }}
        >
          {t.cta_title}
        </motion.h2>
        <p className="text-base sm:text-lg text-slate-500 leading-relaxed mb-10">{t.cta_subtitle}</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/volunteer">
            <Button className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-8 py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200" data-testid="cta-volunteer-btn">
              {t.cta_volunteer}
            </Button>
          </Link>
          <Link to="/donate">
            <Button className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-8 py-3 text-base font-medium shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200" data-testid="cta-donate-btn">
              {t.cta_donate}
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <div data-testid="home-page">
      <HeroSection />
      <RecognitionsTicker />
      <RegisterNudge />
      <MissionsMarquee />
      <MissionsGrid />
      <DrivesSection />
      <CTASection />
    </div>
  );
}

function RecognitionsTicker() {
  const [data, setData] = useState(null);
  useEffect(() => {
    (async () => {
      try { const r = await api.get("/recognitions"); setData(r.data); } catch { setData(null); }
    })();
  }, []);
  if (!data) return null;
  const items = [];
  if (data.top_donor?.name) {
    items.push({ icon: Trophy, label: `Top Donor of FY ${data.fy_label}`, name: data.top_donor.name, sub: `Contribution: \u20B9 ${Number(data.top_donor.amount || 0).toLocaleString("en-IN")}` });
  }
  (data.recent_badges || []).forEach(b => items.push({ icon: Award, label: b.badge, name: b.name }));
  (data.office_bearers || []).forEach(o => items.push({ icon: Compass, label: o.designation, name: o.name }));
  if (!items.length) return null;
  return (
    <section className="py-5 bg-gradient-to-r from-[#0D2847] via-[#1E56A0] to-[#0D2847] border-y border-amber-500/30" data-testid="recognitions-ticker">
      <div className="flex items-center gap-3 px-4">
        <div className="shrink-0 inline-flex items-center gap-2 text-xs text-amber-300 font-medium uppercase tracking-[0.18em]">
          <Star className="w-3.5 h-3.5" /> Heroes of the Hour
        </div>
        <div className="flex-1 overflow-hidden">
          <Marquee gradient={false} speed={40} pauseOnHover className="text-white">
            {items.map((it, i) => {
              const Ic = it.icon;
              return (
                <span key={i} className="inline-flex items-center gap-2 mx-8 text-sm" data-testid={`ticker-item-${i}`}>
                  <Ic className="w-4 h-4 text-amber-300 shrink-0" />
                  <span className="text-amber-200/90 font-medium">{it.label}:</span>
                  <span className="text-white font-semibold">{it.name}</span>
                  {it.sub && <span className="text-white/60 text-xs">· {it.sub}</span>}
                  <span className="text-amber-500/60 mx-3">{'\u2666'}</span>
                </span>
              );
            })}
          </Marquee>
        </div>
      </div>
    </section>
  );
}

function RegisterNudge() {
  const { user } = useAuth();
  if (user) return null;
  return (
    <section className="py-8 bg-gradient-to-r from-amber-50 via-orange-50/60 to-amber-50 border-b border-amber-100" data-testid="register-nudge">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 flex items-center gap-5 flex-wrap justify-between">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-11 h-11 rounded-2xl bg-amber-500/15 border border-amber-300 flex items-center justify-center shrink-0">
            <UserPlus className="w-5 h-5 text-amber-700" />
          </div>
          <div className="min-w-0">
            <p className="text-sm sm:text-base font-semibold text-[#0D2847]">
              Already associated with us, or thinking of joining?
            </p>
            <p className="text-xs sm:text-sm text-stone-600 mt-0.5 max-w-3xl">
              Create a free account so every donation you make is <span className="font-medium text-[#0D2847]">logged against your name</span>, your 80G receipts land in your inbox automatically, and you become eligible for annual recognitions like <span className="italic">Top Donor of the Year</span>, <span className="italic">Star Volunteer</span>, and more.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Link to="/login"><Button variant="outline" className="border-amber-400 text-amber-800 hover:bg-amber-50 rounded-xl" data-testid="nudge-login-btn">I already have an account</Button></Link>
          <Link to="/login"><Button className="bg-amber-600 hover:bg-amber-700 text-white rounded-xl" data-testid="nudge-register-btn"><UserPlus className="w-4 h-4 mr-1.5" /> Register &amp; Compete</Button></Link>
        </div>
      </div>
    </section>
  );
}
