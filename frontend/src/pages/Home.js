import { Link } from "react-router-dom";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MEDIA, MISSIONS_CLIENT } from "../data/missions";
import { Button } from "../components/ui/button";
import { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt, Droplets, ChefHat, ArrowRight } from "lucide-react";
import Marquee from "react-fast-marquee";
import { motion } from "framer-motion";

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
    <div className="bg-[#F5F5F0] py-4 border-y border-stone-200" data-testid="missions-marquee">
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
    <section className="py-20 bg-[#EBF3F9]" data-testid="drives-section">
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
      <MissionsMarquee />
      <MissionsGrid />
      <DrivesSection />
      <CTASection />
    </div>
  );
}
