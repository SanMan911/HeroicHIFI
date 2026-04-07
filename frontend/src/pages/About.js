import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { ORG_INFO, MEDIA } from "../data/missions";
import { motion } from "framer-motion";
import { Building2, Mail, Phone, MapPin, Eye } from "lucide-react";

export default function About() {
  const { lang } = useLang();
  const t = translations[lang].about;

  return (
    <div data-testid="about-page">
      {/* Hero */}
      <section className="relative py-24 sm:py-32 bg-[#1E3A8A] overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <img src={MEDIA.volunteers} alt="" className="w-full h-full object-cover" />
        </div>
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-xs sm:text-sm uppercase tracking-[0.2em] font-semibold text-amber-300 mb-4">
            {t.overline}
          </motion.p>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {t.title}
          </motion.h1>
        </div>
      </section>

      {/* Story */}
      <section className="py-20 sm:py-28">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="space-y-6">
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p1}</p>
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p2}</p>
            <p className="text-base sm:text-lg text-stone-600 leading-relaxed">{t.story_p3}</p>
          </motion.div>
        </div>
      </section>

      {/* Vision */}
      <section className="py-20 bg-[#F5F5F0]" data-testid="vision-section">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[#1E3A8A]/10 flex items-center justify-center mx-auto mb-6">
            <Eye className="w-8 h-8 text-[#1E3A8A]" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#1C1917] mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.vision_title}
          </h2>
          <p className="text-base sm:text-lg text-stone-600 leading-relaxed max-w-3xl mx-auto">{t.vision_text}</p>
        </div>
      </section>

      {/* Legal Info */}
      <section className="py-20 sm:py-28" data-testid="legal-section">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h2 className="text-3xl sm:text-4xl font-medium tracking-tight text-[#1C1917] mb-10 text-center" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.legal_title}
          </h2>
          <div className="bg-white rounded-2xl p-8 sm:p-10 shadow-sm border border-stone-200 space-y-6">
            <div className="flex items-start gap-4">
              <Building2 className="w-5 h-5 text-[#1E3A8A] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.cin}</p>
                <p className="text-base font-semibold text-[#1C1917] font-mono">{ORG_INFO.cin}</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <MapPin className="w-5 h-5 text-[#1E3A8A] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.registered_address}</p>
                <p className="text-base text-[#1C1917]">{ORG_INFO.address}</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Mail className="w-5 h-5 text-[#1E3A8A] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.email}</p>
                <a href={`mailto:${ORG_INFO.email}`} className="text-base text-[#1E3A8A] hover:underline">{ORG_INFO.email}</a>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Phone className="w-5 h-5 text-[#1E3A8A] mt-1 shrink-0" />
              <div>
                <p className="text-sm font-medium text-stone-500 mb-1">{t.phone}</p>
                <a href={`tel:${ORG_INFO.phone}`} className="text-base text-[#1E3A8A] hover:underline">{ORG_INFO.phone}</a>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
