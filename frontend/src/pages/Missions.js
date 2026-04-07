import { Link } from "react-router-dom";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { MISSIONS_CLIENT } from "../data/missions";
import { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

const iconMap = { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt };

export default function Missions() {
  const { lang } = useLang();
  const t = translations[lang];

  return (
    <div data-testid="missions-page">
      <section className="relative py-24 sm:py-32 bg-[#1E3A8A]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-amber-300 mb-4"
          >
            {t.home.missions_subtitle}
          </motion.p>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.nav.missions}
          </motion.h1>
        </div>
      </section>

      <section className="py-20 sm:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {MISSIONS_CLIENT.map((mission, i) => {
              const Icon = iconMap[mission.icon];
              return (
                <motion.div
                  key={mission.slug}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                >
                  <Link to={`/missions/${mission.slug}`} className="group block" data-testid={`mission-link-${mission.slug}`}>
                    <div className="bg-white rounded-2xl overflow-hidden border border-stone-200 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                      <div className="relative h-52 overflow-hidden">
                        <img src={mission.image} alt={mission.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                        <div className="absolute top-4 left-4">
                          <div className="w-10 h-10 rounded-full flex items-center justify-center shadow-md" style={{ backgroundColor: mission.color }}>
                            {Icon && <Icon className="w-5 h-5 text-white" />}
                          </div>
                        </div>
                      </div>
                      <div className="p-6">
                        <h3 className="text-xl sm:text-2xl font-medium text-[#1C1917] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                          {lang === "hi" ? mission.name_hi : mission.name}
                        </h3>
                        <p className="text-sm text-stone-500 mb-4">{lang === "hi" ? mission.tagline_hi : mission.tagline}</p>
                        <span className="inline-flex items-center gap-1 text-sm font-medium text-[#1E3A8A] group-hover:gap-2 transition-all">
                          {lang === "hi" ? "और जानें" : "Learn More"} <ArrowRight className="w-4 h-4" />
                        </span>
                      </div>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
